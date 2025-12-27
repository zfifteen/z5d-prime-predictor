#!/usr/bin/env python3
"""
Z-Shared: Centralized precision, seed, and transform utilities
================================================================

Single source of truth for:
- Precision handling (DPS_MIN, DPS_TARGET, DPS_MAX)
- Seed & RNG control (SEED, RNG_KIND)
- Shared φ-/Z-transforms and Dirichlet/angle helpers

This module enforces deterministic behavior and prevents precision drift.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import gmpy2 as gp
import numpy as np

# ============================================================================
# PRECISION CONSTANTS
# ============================================================================

DPS_MIN = 50  # Minimum decimal precision
DPS_TARGET = 256  # Target decimal precision for most operations
DPS_MAX = 1024  # Maximum decimal precision for extreme ranges

# Precision thresholds by magnitude
PRECISION_TABLE = {
    1e14: 128,
    1e15: 160,
    1e16: 192,
    1e17: 224,
    1e18: 256,
    1e20: 320,
}


def get_required_precision(n: float) -> int:
    """
    Return required decimal precision for magnitude N.
    
    Args:
        n: Magnitude to compute precision for
        
    Returns:
        Required decimal places (DPS)
    """
    for threshold, dps in sorted(PRECISION_TABLE.items()):
        if n < threshold:
            return dps
    return DPS_MAX


def assert_dps(n: float, actual_dps: int) -> None:
    """
    Assert that actual precision meets requirements for magnitude N.
    
    Args:
        n: Magnitude being processed
        actual_dps: Actual decimal precision in use
        
    Raises:
        ValueError: If precision is insufficient
    """
    required = get_required_precision(n)
    if actual_dps < required:
        raise ValueError(
            f"Insufficient precision for N={n:.2e}: "
            f"required {required} DPS, got {actual_dps} DPS"
        )
    if actual_dps < DPS_MIN:
        raise ValueError(
            f"Precision {actual_dps} DPS below minimum {DPS_MIN} DPS"
        )


def set_gmpy2_precision(n: float) -> gp.context:
    """
    Set gmpy2 precision appropriate for magnitude N.
    
    Args:
        n: Magnitude to compute precision for
        
    Returns:
        gmpy2 context with precision set
    """
    dps = get_required_precision(n)
    # Convert DPS to bits (approximately 3.32 bits per decimal digit)
    bits = int(dps * 3.32) + 64  # Add slack
    ctx = gp.context()
    ctx.precision = bits
    return ctx


# ============================================================================
# SEED & RNG CONTROL
# ============================================================================

SEED_DEFAULT = 42
RNG_KIND_DEFAULT = "PCG64"  # Options: PCG64, MT19937, Philox

_global_seed: Optional[int] = None
_global_rng_kind: Optional[str] = None


def set_seed(seed: int, rng_kind: str = RNG_KIND_DEFAULT) -> None:
    """
    Set global seed for reproducibility.
    
    Args:
        seed: Random seed value
        rng_kind: RNG algorithm (PCG64, MT19937, Philox)
    """
    global _global_seed, _global_rng_kind
    _global_seed = seed
    _global_rng_kind = rng_kind
    np.random.seed(seed)


def assert_seed() -> None:
    """
    Assert that seed has been set.
    
    Raises:
        RuntimeError: If seed has not been initialized
    """
    if _global_seed is None:
        raise RuntimeError(
            "Seed not initialized. Call set_seed() before using RNG operations."
        )


def get_seed_info() -> Dict[str, Any]:
    """
    Get current seed configuration.
    
    Returns:
        Dictionary with seed, rng_kind, and status
    """
    assert_seed()
    return {
        "seed": _global_seed,
        "rng_kind": _global_rng_kind,
        "initialized": True,
    }


def create_rng(seed: Optional[int] = None) -> np.random.Generator:
    """
    Create numpy RNG with specified or global seed.
    
    Args:
        seed: Optional seed override
        
    Returns:
        Numpy random generator
    """
    if seed is None:
        assert_seed()
        seed = _global_seed
    
    if _global_rng_kind == "PCG64":
        bit_gen = np.random.PCG64(seed)
    elif _global_rng_kind == "MT19937":
        bit_gen = np.random.MT19937(seed)
    elif _global_rng_kind == "Philox":
        bit_gen = np.random.Philox(seed)
    else:
        raise ValueError(f"Unknown RNG kind: {_global_rng_kind}")
    
    return np.random.Generator(bit_gen)


# ============================================================================
# SHARED TRANSFORMS
# ============================================================================

# Golden ratio (φ)
PHI = gp.mpfr("1.618033988749894848204586834365638117720309179805762862135448622705260462818902449707207204189391137484754088075386891752126633862223536931793180060766726354433389086595939582905638322661319928290267880675208766892501711696207032221043216269548626296313614438149758701220340805887954454749246185695364864449241044320771344947049565846788509874339442212544877066478091588460749988712400765217057517978834166256249407589069704000281210427621771117778053153171410117046665991466979873176135600670874807101317952368942752194843530567830022878569978297783478458782289110976250030269615617002504643382437764861028383126833037242926752631165339247316711121158818638513316203840052221657912866752946549068113171599343235973494985090409476213222981017261070596116456299098162905552085247903524060201727997471753427775927786256194320827")


def phi_transform(x: float, power: float = 1.0) -> gp.mpfr:
    """
    Apply φ (golden ratio) transform to value.
    
    Args:
        x: Input value
        power: Power to raise φ to (default 1.0)
        
    Returns:
        φ^power * x
    """
    return gp.mpfr(PHI ** power) * gp.mpfr(x)


def z_transform(n: float, k: float) -> gp.mpfr:
    """
    Apply Z-transform: combines geometric and logarithmic scaling.
    
    Args:
        n: Base magnitude
        k: Index parameter
        
    Returns:
        Z-transformed value
    """
    ctx = set_gmpy2_precision(n)
    old_ctx = gp.get_context()
    gp.set_context(ctx)
    try:
        n_mpfr = gp.mpfr(n)
        k_mpfr = gp.mpfr(k)
        ln_n = gp.log(n_mpfr)
        ln_k = gp.log(k_mpfr) if k > 1 else gp.mpfr(0)
        return n_mpfr * gp.sqrt(k_mpfr) / (ln_n + ln_k + 1)
    finally:
        gp.set_context(old_ctx)


def dirichlet_phase(n: float, k: float, harmonic: int = 1) -> gp.mpfr:
    """
    Compute Dirichlet-style phase angle.
    
    Args:
        n: Base magnitude
        k: Index parameter
        harmonic: Harmonic number (default 1)
        
    Returns:
        Phase angle in radians
    """
    ctx = set_gmpy2_precision(n)
    old_ctx = gp.get_context()
    gp.set_context(ctx)
    try:
        n_mpfr = gp.mpfr(n)
        k_mpfr = gp.mpfr(k)
        phase = gp.mpfr(2) * gp.const_pi() * harmonic * k_mpfr / gp.sqrt(n_mpfr)
        return phase
    finally:
        gp.set_context(old_ctx)


# ============================================================================
# I/O SCHEMA AND LOGGING
# ============================================================================

SCHEMA_VERSION = "1.0.0"

# Standard column names for unified output
STANDARD_COLUMNS = [
    "run_id",
    "N",
    "seed",
    "dps",
    "k",
    "pair_rank",
    "p",
    "q",
    "score_resonance",
    "score_z5d",
    "agree",
    "ts",
]


def create_run_metadata(
    run_id: str,
    n_values: list,
    description: str,
    extra: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create standardized run metadata.
    
    Args:
        run_id: Unique run identifier
        n_values: List of N values being processed
        description: Human-readable description
        extra: Optional additional metadata
        
    Returns:
        Metadata dictionary
    """
    assert_seed()
    seed_info = get_seed_info()
    
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "description": description,
        "seed": seed_info["seed"],
        "rng_kind": seed_info["rng_kind"],
        "dps_min": DPS_MIN,
        "dps_target": DPS_TARGET,
        "dps_max": DPS_MAX,
        "n_values": n_values,
        "n_count": len(n_values),
    }
    
    if extra:
        metadata.update(extra)
    
    return metadata


def write_jsonl_with_metadata(
    path: Path,
    records: list,
    metadata: Dict[str, Any]
) -> None:
    """
    Write JSONL file with metadata header.
    
    Args:
        path: Output path
        records: List of record dictionaries
        metadata: Metadata dictionary
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with path.open("w") as f:
        # Write metadata as first line
        f.write(json.dumps({"_metadata": metadata}) + "\n")
        
        # Write records
        for record in records:
            f.write(json.dumps(record) + "\n")


def read_jsonl_with_metadata(path: Path) -> tuple[Dict[str, Any], list]:
    """
    Read JSONL file with metadata header.
    
    Args:
        path: Input path
        
    Returns:
        Tuple of (metadata, records)
    """
    with path.open("r") as f:
        # Read first line as metadata
        first_line = f.readline()
        metadata_obj = json.loads(first_line)
        metadata = metadata_obj.get("_metadata", {})
        
        # Read remaining records
        records = []
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    
    return metadata, records


def compute_file_hash(path: Path) -> str:
    """
    Compute SHA-256 hash of file.
    
    Args:
        path: File path
        
    Returns:
        Hex digest of SHA-256 hash
    """
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


# ============================================================================
# LOGGING
# ============================================================================

def log_precision_info(n: float, actual_dps: int) -> None:
    """
    Log precision information for debugging.
    
    Args:
        n: Magnitude being processed
        actual_dps: Actual decimal precision
    """
    required = get_required_precision(n)
    status = "✓" if actual_dps >= required else "✗"
    print(
        f"[PRECISION] N={n:.2e} required={required} actual={actual_dps} {status}",
        file=sys.stderr
    )


def log_seed_info() -> None:
    """Log seed configuration."""
    try:
        info = get_seed_info()
        print(
            f"[SEED] seed={info['seed']} rng_kind={info['rng_kind']}",
            file=sys.stderr
        )
    except RuntimeError:
        print("[SEED] ✗ Not initialized", file=sys.stderr)


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize(seed: int = SEED_DEFAULT, rng_kind: str = RNG_KIND_DEFAULT) -> None:
    """
    Initialize z_shared module with seed and RNG.
    
    Args:
        seed: Random seed
        rng_kind: RNG algorithm
    """
    set_seed(seed, rng_kind)
    log_seed_info()


if __name__ == "__main__":
    # Test initialization
    initialize()
    
    # Test precision
    for n in [1e14, 1e15, 1e16, 1e17, 1e18]:
        dps = get_required_precision(n)
        log_precision_info(n, dps)
        assert_dps(n, dps)
    
    # Test transforms
    print(f"φ = {PHI}")
    print(f"φ * 100 = {phi_transform(100)}")
    print(f"Z(1e15, 1000) = {z_transform(1e15, 1000)}")
    print(f"Dirichlet phase(1e15, 1000) = {dirichlet_phase(1e15, 1000)}")
    
    print("\n✓ z_shared module tests passed")
