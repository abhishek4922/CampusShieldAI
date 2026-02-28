"""
CampusShield AI — AMD CPU Optimization Module

Documents and implements AMD-specific performance tuning for
the ML inference pipeline.

WHY AMD EPYC IS IDEAL FOR THIS WORKLOAD:
  - EPYC 9004 (Genoa): 96–128 cores per socket → massive parallelism
    for concurrent phishing scan requests
  - Large L3 cache (256–384 MB) → sklearn feature matrices fit in cache
  - High memory bandwidth → fast numpy operation on email batches
  - NUMA-aware topology: containers should be pinned to CCX clusters

AMD INSTINCT GPU (MI300X) SUPPORT:
  - ROCm-compatible PyTorch/transformer models can run on MI300X
  - For HuggingFace transformer-based text classification:
    set ROCR_VISIBLE_DEVICES and install torch-rocm

IMPLEMENTATION STRATEGIES:
  1. joblib with n_jobs=-1 → uses all available physical cores
  2. threadpoolctl: control BLAS thread count per worker process
  3. ProcessPoolExecutor for batch inference (CPU-bound)
  4. ONNX Runtime with OpenVINO EP: compiled model inference
     runs ~3-10x faster than raw sklearn predict()
"""

import os
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from typing import List, Callable, TypeVar, Any

T = TypeVar("T")


def configure_amd_threading():
    """
    Set environment variables for optimal AMD EPYC thread utilisation.
    Call this ONCE at service startup before any numpy/sklearn imports.

    With AMD EPYC:
    - OMP_NUM_THREADS=0 → OpenMP uses all available cores (default)
    - OPENBLAS_NUM_THREADS follows OMP
    - Setting these after process start has no effect; they must be
      set before numpy is first imported (hence startup-only call).
    """
    cpu_count = multiprocessing.cpu_count()

    # Allow sklearn to use all cores for parallel estimators
    os.environ.setdefault("OMP_NUM_THREADS",     str(cpu_count))
    os.environ.setdefault("OPENBLAS_NUM_THREADS", str(cpu_count))
    os.environ.setdefault("MKL_NUM_THREADS",      str(cpu_count))
    os.environ.setdefault("VECLIB_MAXIMUM_THREADS", str(cpu_count))
    os.environ.setdefault("NUMEXPR_NUM_THREADS",  str(cpu_count))

    return cpu_count


def get_optimal_workers() -> int:
    """
    Determine optimal number of worker processes for batch inference.

    AMD EPYC recommendation: 1 worker per CCX cluster (typically 8 cores).
    For a 96-core EPYC 9654: floor(96/8) = 12 workers.
    """
    cpu_count = multiprocessing.cpu_count()
    # Heuristic: 1 worker per 8 cores (matches AMD CCX cluster size)
    return max(1, cpu_count // 8)


class AMDParallelInferencePool:
    """
    Process pool for parallel phishing scan inference.
    Each process gets its own GIL-free CPU core (AMD EPYC CCX).

    Usage:
        pool = AMDParallelInferencePool()
        results = await pool.map(analyze_function, list_of_requests)
    """

    def __init__(self):
        self._workers = get_optimal_workers()
        self._executor = ProcessPoolExecutor(max_workers=self._workers)

    def map(self, fn: Callable, items: List[Any]) -> List[Any]:
        """Distribute items across worker processes and collect results."""
        return list(self._executor.map(fn, items))

    def shutdown(self):
        self._executor.shutdown(wait=True)

    def __repr__(self):
        return f"AMDParallelInferencePool(workers={self._workers}, cpu_cores={multiprocessing.cpu_count()})"
