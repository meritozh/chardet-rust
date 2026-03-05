#!/usr/bin/env python3
"""Benchmark demo for chardet Rust implementation."""

from __future__ import annotations

import time

import chardet


def benchmark_detection(description: str, data: bytes, iterations: int = 1000) -> float:
    """Benchmark detection and return calls per second."""
    # Warmup
    for _ in range(10):
        chardet.detect(data)
    
    start = time.perf_counter()
    for _ in range(iterations):
        chardet.detect(data)
    elapsed = time.perf_counter() - start
    
    calls_per_sec = iterations / elapsed
    per_call_us = (elapsed / iterations) * 1_000_000
    
    print(f"{description}:")
    print(f"  {calls_per_sec:,.0f} calls/sec ({per_call_us:.1f} μs/call)")
    
    return calls_per_sec


def main():
    print("=" * 60)
    print("Chardet Rust Implementation - Performance Benchmark")
    print("=" * 60)
    print()
    
    # Test 1: Pure ASCII
    benchmark_detection(
        "Pure ASCII (4KB)",
        b"Hello world, this is a plain ASCII text. " * 100,
        iterations=5000
    )
    print()
    
    # Test 2: UTF-8 with multibyte characters
    benchmark_detection(
        "UTF-8 with accents (4KB)",
        "Héllo wörld café résumé naïve".encode() * 150,
        iterations=5000
    )
    print()
    
    # Test 3: BOM detection
    benchmark_detection(
        "UTF-8 with BOM (4KB)",
        b"\xef\xbb\xbfHello world" * 200,
        iterations=10000
    )
    print()
    
    # Test 4: Japanese (Shift_JIS)
    benchmark_detection(
        "Japanese Shift_JIS (4KB)",
        "こんにちは世界".encode("shift_jis") * 400,
        iterations=2000
    )
    print()
    
    # Test 5: Mixed content
    benchmark_detection(
        "Mixed content (20KB)",
        b"Hello world! " * 1000 + "Héllo wörld! ".encode() * 500,
        iterations=1000
    )
    print()
    
    # Test 6: Large file simulation
    print("Large file (100KB):")
    large_data = b"The quick brown fox jumps over the lazy dog. " * 2000
    start = time.perf_counter()
    result = chardet.detect(large_data)
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  {elapsed:.2f}ms for single 100KB file")
    print(f"  Result: {result}")
    print()
    
    # Test 7: detect_all performance
    print("detect_all() performance:")
    data = "Héllo wörld café".encode()
    start = time.perf_counter()
    for _ in range(1000):
        chardet.detect_all(data)
    elapsed = time.perf_counter() - start
    calls_per_sec = 1000 / elapsed
    print(f"  {calls_per_sec:,.0f} calls/sec")
    print()
    
    print("=" * 60)
    print("Benchmark complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
