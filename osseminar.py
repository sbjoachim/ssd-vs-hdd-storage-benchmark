
#!/usr/bin/env python3
"""
Mass-Storage Performance Benchmark Tool
COSC 2667 Operating Systems Project
Author: Joachim Brian - 0686270

This tool measures and compares storage device performance metrics:
- Sequential Read/Write speeds
- Random Read/Write speeds (IOPS)
- Access latency
- Throughput under different block sizes

Usage: python storage_benchmark.py [test_directory]
"""

import os
import time
import random
import statistics
import json
from pathlib import Path

# Configuration
TEST_FILE_SIZE_MB = 100  # Size of test file in MB
BLOCK_SIZES = [4096, 16384, 65536, 262144, 1048576]  # 4KB, 16KB, 64KB, 256KB, 1MB
RANDOM_OPS_COUNT = 1000  # Number of random I/O operations
ITERATIONS = 3  # Number of test iterations for averaging


class StorageBenchmark:
    def __init__(self, test_dir="./benchmark_test"):
        self.test_dir = Path(test_dir)
        self.test_dir.mkdir(exist_ok=True)
        self.test_file = self.test_dir / "benchmark_test_file.dat"
        self.results = {}
    
    def generate_random_data(self, size_bytes):
        """Generate random data for writing"""
        return os.urandom(size_bytes)
    
    def sequential_write_test(self, file_size_mb, block_size):
        """Measure sequential write speed"""
        total_bytes = file_size_mb * 1024 * 1024
        data = self.generate_random_data(block_size)
        
        start_time = time.perf_counter()
        with open(self.test_file, 'wb') as f:
            bytes_written = 0
            while bytes_written < total_bytes:
                f.write(data)
                bytes_written += block_size
            f.flush()
            os.fsync(f.fileno())  # Force write to disk
        end_time = time.perf_counter()
        
        elapsed = end_time - start_time
        speed_mbps = (total_bytes / (1024 * 1024)) / elapsed
        return speed_mbps, elapsed
    
    def sequential_read_test(self, block_size):
        """Measure sequential read speed"""
        file_size = os.path.getsize(self.test_file)
        
        # Clear OS cache (best effort)
        start_time = time.perf_counter()
        with open(self.test_file, 'rb') as f:
            while f.read(block_size):
                pass
        end_time = time.perf_counter()
        
        elapsed = end_time - start_time
        speed_mbps = (file_size / (1024 * 1024)) / elapsed
        return speed_mbps, elapsed
    
    def random_read_test(self, block_size, num_ops):
        """Measure random read performance (IOPS)"""
        file_size = os.path.getsize(self.test_file)
        max_offset = file_size - block_size
        
        # Generate random offsets
        offsets = [random.randint(0, max_offset) for _ in range(num_ops)]
        
        latencies = []
        start_time = time.perf_counter()
        with open(self.test_file, 'rb') as f:
            for offset in offsets:
                op_start = time.perf_counter()
                f.seek(offset)
                f.read(block_size)
                op_end = time.perf_counter()
                latencies.append((op_end - op_start) * 1000)  # Convert to ms
        end_time = time.perf_counter()
        
        elapsed = end_time - start_time
        iops = num_ops / elapsed
        avg_latency = statistics.mean(latencies)
        
        return iops, avg_latency, elapsed
    
    def random_write_test(self, block_size, num_ops):
        """Measure random write performance (IOPS)"""
        file_size = os.path.getsize(self.test_file)
        max_offset = file_size - block_size
        data = self.generate_random_data(block_size)
        
        offsets = [random.randint(0, max_offset) for _ in range(num_ops)]
        
        latencies = []
        start_time = time.perf_counter()
        with open(self.test_file, 'r+b') as f:
            for offset in offsets:
                op_start = time.perf_counter()
                f.seek(offset)
                f.write(data)
                op_end = time.perf_counter()
                latencies.append((op_end - op_start) * 1000)
            f.flush()
            os.fsync(f.fileno())
        end_time = time.perf_counter()
        
        elapsed = end_time - start_time
        iops = num_ops / elapsed
        avg_latency = statistics.mean(latencies)
        
        return iops, avg_latency, elapsed
    
    def run_full_benchmark(self):
        """Run complete benchmark suite"""
        print("=" * 60)
        print("MASS-STORAGE PERFORMANCE BENCHMARK")
        print("COSC 2667 Operating Systems Project")
        print("=" * 60)
        print(f"\nTest Directory: {self.test_dir.absolute()}")
        print(f"Test File Size: {TEST_FILE_SIZE_MB} MB")
        print(f"Iterations: {ITERATIONS}")
        print("-" * 60)
        
        results = {
            "sequential_write": {},
            "sequential_read": {},
            "random_read": {},
            "random_write": {},
            "metadata": {
                "test_file_size_mb": TEST_FILE_SIZE_MB,
                "iterations": ITERATIONS,
                "random_ops": RANDOM_OPS_COUNT
            }
        }
        
        for block_size in BLOCK_SIZES:
            bs_label = self._format_size(block_size)
            print(f"\n>>> Testing with Block Size: {bs_label}")
            
            # Sequential Write
            print(f"  Sequential Write...", end=" ", flush=True)
            write_speeds = []
            for _ in range(ITERATIONS):
                speed, _ = self.sequential_write_test(TEST_FILE_SIZE_MB, block_size)
                write_speeds.append(speed)
            avg_write = statistics.mean(write_speeds)
            results["sequential_write"][bs_label] = round(avg_write, 2)
            print(f"{avg_write:.2f} MB/s")
            
            # Sequential Read
            print(f"  Sequential Read...", end=" ", flush=True)
            read_speeds = []
            for _ in range(ITERATIONS):
                speed, _ = self.sequential_read_test(block_size)
                read_speeds.append(speed)
            avg_read = statistics.mean(read_speeds)
            results["sequential_read"][bs_label] = round(avg_read, 2)
            print(f"{avg_read:.2f} MB/s")
            
            # Random Read
            print(f"  Random Read...", end=" ", flush=True)
            iops_list = []
            latency_list = []
            for _ in range(ITERATIONS):
                iops, latency, _ = self.random_read_test(block_size, RANDOM_OPS_COUNT)
                iops_list.append(iops)
                latency_list.append(latency)
            avg_iops = statistics.mean(iops_list)
            avg_lat = statistics.mean(latency_list)
            results["random_read"][bs_label] = {
                "iops": round(avg_iops, 2),
                "latency_ms": round(avg_lat, 4)
            }
            print(f"{avg_iops:.2f} IOPS, {avg_lat:.4f} ms avg latency")
            
            # Random Write
            print(f"  Random Write...", end=" ", flush=True)
            iops_list = []
            latency_list = []
            for _ in range(ITERATIONS):
                iops, latency, _ = self.random_write_test(block_size, RANDOM_OPS_COUNT)
                iops_list.append(iops)
                latency_list.append(latency)
            avg_iops = statistics.mean(iops_list)
            avg_lat = statistics.mean(latency_list)
            results["random_write"][bs_label] = {
                "iops": round(avg_iops, 2),
                "latency_ms": round(avg_lat, 4)
            }
            print(f"{avg_iops:.2f} IOPS, {avg_lat:.4f} ms avg latency")
        
        # Cleanup
        self._cleanup()
        
        # Save results
        results_file = self.test_dir / "benchmark_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n[Results saved to {results_file}]")
        
        self._print_summary(results)
        return results
    
    def _format_size(self, size_bytes):
        """Format bytes to human readable"""
        if size_bytes >= 1048576:
            return f"{size_bytes // 1048576}MB"
        elif size_bytes >= 1024:
            return f"{size_bytes // 1024}KB"
        return f"{size_bytes}B"
    
    def _cleanup(self):
        """Remove test files"""
        if self.test_file.exists():
            self.test_file.unlink()
    
    def _print_summary(self, results):
        """Print formatted summary table"""
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        
        print("\nSequential Performance (MB/s):")
        print("-" * 40)
        print(f"{'Block Size':<12} {'Write':<15} {'Read':<15}")
        print("-" * 40)
        for bs in results["sequential_write"]:
            write = results["sequential_write"][bs]
            read = results["sequential_read"][bs]
            print(f"{bs:<12} {write:<15.2f} {read:<15.2f}")
        
        print("\nRandom Performance (IOPS):")
        print("-" * 50)
        print(f"{'Block Size':<12} {'Read IOPS':<15} {'Write IOPS':<15}")
        print("-" * 50)
        for bs in results["random_read"]:
            read_iops = results["random_read"][bs]["iops"]
            write_iops = results["random_write"][bs]["iops"]
            print(f"{bs:<12} {read_iops:<15.2f} {write_iops:<15.2f}")
        
        print("\nRandom Latency (ms):")
        print("-" * 50)
        print(f"{'Block Size':<12} {'Read Lat':<15} {'Write Lat':<15}")
        print("-" * 50)
        for bs in results["random_read"]:
            read_lat = results["random_read"][bs]["latency_ms"]
            write_lat = results["random_write"][bs]["latency_ms"]
            print(f"{bs:<12} {read_lat:<15.4f} {write_lat:<15.4f}")


# Simulated comparison data (HDD vs SSD typical values)
# Used for report generation when actual hardware isn't available
SIMULATED_HDD_DATA = {
    "sequential_write": {"4KB": 95.5, "16KB": 110.2, "64KB": 125.8, "256KB": 140.3, "1MB": 155.7},
    "sequential_read": {"4KB": 105.2, "16KB": 122.4, "64KB": 145.6, "256KB": 165.3, "1MB": 180.5},
    "random_read": {
        "4KB": {"iops": 85.3, "latency_ms": 11.72},
        "16KB": {"iops": 78.5, "latency_ms": 12.74},
        "64KB": {"iops": 65.2, "latency_ms": 15.34},
        "256KB": {"iops": 45.8, "latency_ms": 21.83},
        "1MB": {"iops": 28.4, "latency_ms": 35.21}
    },
    "random_write": {
        "4KB": {"iops": 75.6, "latency_ms": 13.23},
        "16KB": {"iops": 68.9, "latency_ms": 14.51},
        "64KB": {"iops": 55.3, "latency_ms": 18.08},
        "256KB": {"iops": 38.7, "latency_ms": 25.84},
        "1MB": {"iops": 22.1, "latency_ms": 45.25}
    }
}

SIMULATED_SSD_DATA = {
    "sequential_write": {"4KB": 485.3, "16KB": 510.7, "64KB": 535.2, "256KB": 548.9, "1MB": 555.4},
    "sequential_read": {"4KB": 520.6, "16KB": 545.8, "64KB": 558.3, "256KB": 565.1, "1MB": 570.2},
    "random_read": {
        "4KB": {"iops": 95000.5, "latency_ms": 0.0105},
        "16KB": {"iops": 75000.3, "latency_ms": 0.0133},
        "64KB": {"iops": 45000.8, "latency_ms": 0.0222},
        "256KB": {"iops": 18000.2, "latency_ms": 0.0556},
        "1MB": {"iops": 5500.6, "latency_ms": 0.1818}
    },
    "random_write": {
        "4KB": {"iops": 85000.2, "latency_ms": 0.0118},
        "16KB": {"iops": 68000.5, "latency_ms": 0.0147},
        "64KB": {"iops": 38000.3, "latency_ms": 0.0263},
        "256KB": {"iops": 15000.8, "latency_ms": 0.0667},
        "1MB": {"iops": 4800.4, "latency_ms": 0.2083}
    }
}


def generate_comparison_report():
    """Generate comparison data for report"""
    print("\n" + "=" * 70)
    print("HDD vs SSD PERFORMANCE COMPARISON")
    print("(Based on typical consumer-grade devices)")
    print("=" * 70)
    
    print("\n[1] SEQUENTIAL PERFORMANCE COMPARISON (MB/s)")
    print("-" * 60)
    print(f"{'Block Size':<12} {'HDD Write':<12} {'SSD Write':<12} {'Speedup':<10}")
    print("-" * 60)
    for bs in SIMULATED_HDD_DATA["sequential_write"]:
        hdd = SIMULATED_HDD_DATA["sequential_write"][bs]
        ssd = SIMULATED_SSD_DATA["sequential_write"][bs]
        speedup = ssd / hdd
        print(f"{bs:<12} {hdd:<12.1f} {ssd:<12.1f} {speedup:.1f}x")
    
    print("\n[2] RANDOM READ IOPS COMPARISON")
    print("-" * 60)
    print(f"{'Block Size':<12} {'HDD IOPS':<15} {'SSD IOPS':<15} {'Speedup':<10}")
    print("-" * 60)
    for bs in SIMULATED_HDD_DATA["random_read"]:
        hdd = SIMULATED_HDD_DATA["random_read"][bs]["iops"]
        ssd = SIMULATED_SSD_DATA["random_read"][bs]["iops"]
        speedup = ssd / hdd
        print(f"{bs:<12} {hdd:<15.1f} {ssd:<15.1f} {speedup:.0f}x")
    
    print("\n[3] RANDOM READ LATENCY COMPARISON (ms)")
    print("-" * 60)
    print(f"{'Block Size':<12} {'HDD Latency':<15} {'SSD Latency':<15} {'Reduction':<10}")
    print("-" * 60)
    for bs in SIMULATED_HDD_DATA["random_read"]:
        hdd = SIMULATED_HDD_DATA["random_read"][bs]["latency_ms"]
        ssd = SIMULATED_SSD_DATA["random_read"][bs]["latency_ms"]
        reduction = hdd / ssd
        print(f"{bs:<12} {hdd:<15.4f} {ssd:<15.4f} {reduction:.0f}x faster")
    
    print("\n" + "=" * 70)
    print("KEY FINDINGS:")
    print("-" * 70)
    print("- SSD sequential write is ~3.5x faster than HDD")
    print("- SSD random read IOPS is ~1000x higher than HDD")
    print("- SSD latency is ~1000x lower than HDD for random operations")
    print("- The gap widens significantly for small block random I/O")
    print("=" * 70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--compare":
        generate_comparison_report()
    else:
        test_dir = sys.argv[1] if len(sys.argv) > 1 else "./benchmark_test"
        benchmark = StorageBenchmark(test_dir)
        benchmark.run_full_benchmark()
        #!/usr/bin/env python3
"""
Mass-Storage Performance Benchmark Tool
COSC 2667 Operating Systems Project
Author: Joachim Brian - 0686270

This tool measures and compares storage device performance metrics:
- Sequential Read/Write speeds
- Random Read/Write speeds (IOPS)
- Access latency
- Throughput under different block sizes

Usage: python storage_benchmark.py [test_directory]
"""

import os
import time
import random
import statistics
import json
from pathlib import Path

# Configuration
TEST_FILE_SIZE_MB = 100  # Size of test file in MB
BLOCK_SIZES = [4096, 16384, 65536, 262144, 1048576]  # 4KB, 16KB, 64KB, 256KB, 1MB
RANDOM_OPS_COUNT = 1000  # Number of random I/O operations
ITERATIONS = 3  # Number of test iterations for averaging


class StorageBenchmark:
    def __init__(self, test_dir="./benchmark_test"):
        self.test_dir = Path(test_dir)
        self.test_dir.mkdir(exist_ok=True)
        self.test_file = self.test_dir / "benchmark_test_file.dat"
        self.results = {}
    
    def generate_random_data(self, size_bytes):
        """Generate random data for writing"""
        return os.urandom(size_bytes)
    
    def sequential_write_test(self, file_size_mb, block_size):
        """Measure sequential write speed"""
        total_bytes = file_size_mb * 1024 * 1024
        data = self.generate_random_data(block_size)
        
        start_time = time.perf_counter()
        with open(self.test_file, 'wb') as f:
            bytes_written = 0
            while bytes_written < total_bytes:
                f.write(data)
                bytes_written += block_size
            f.flush()
            os.fsync(f.fileno())  # Force write to disk
        end_time = time.perf_counter()
        
        elapsed = end_time - start_time
        speed_mbps = (total_bytes / (1024 * 1024)) / elapsed
        return speed_mbps, elapsed
    
    def sequential_read_test(self, block_size):
        """Measure sequential read speed"""
        file_size = os.path.getsize(self.test_file)
        
        # Clear OS cache (best effort)
        start_time = time.perf_counter()
        with open(self.test_file, 'rb') as f:
            while f.read(block_size):
                pass
        end_time = time.perf_counter()
        
        elapsed = end_time - start_time
        speed_mbps = (file_size / (1024 * 1024)) / elapsed
        return speed_mbps, elapsed
    
    def random_read_test(self, block_size, num_ops):
        """Measure random read performance (IOPS)"""
        file_size = os.path.getsize(self.test_file)
        max_offset = file_size - block_size
        
        # Generate random offsets
        offsets = [random.randint(0, max_offset) for _ in range(num_ops)]
        
        latencies = []
        start_time = time.perf_counter()
        with open(self.test_file, 'rb') as f:
            for offset in offsets:
                op_start = time.perf_counter()
                f.seek(offset)
                f.read(block_size)
                op_end = time.perf_counter()
                latencies.append((op_end - op_start) * 1000)  # Convert to ms
        end_time = time.perf_counter()
        
        elapsed = end_time - start_time
        iops = num_ops / elapsed
        avg_latency = statistics.mean(latencies)
        
        return iops, avg_latency, elapsed
    
    def random_write_test(self, block_size, num_ops):
        """Measure random write performance (IOPS)"""
        file_size = os.path.getsize(self.test_file)
        max_offset = file_size - block_size
        data = self.generate_random_data(block_size)
        
        offsets = [random.randint(0, max_offset) for _ in range(num_ops)]
        
        latencies = []
        start_time = time.perf_counter()
        with open(self.test_file, 'r+b') as f:
            for offset in offsets:
                op_start = time.perf_counter()
                f.seek(offset)
                f.write(data)
                op_end = time.perf_counter()
                latencies.append((op_end - op_start) * 1000)
            f.flush()
            os.fsync(f.fileno())
        end_time = time.perf_counter()
        
        elapsed = end_time - start_time
        iops = num_ops / elapsed
        avg_latency = statistics.mean(latencies)
        
        return iops, avg_latency, elapsed
    
    def run_full_benchmark(self):
        """Run complete benchmark suite"""
        print("=" * 60)
        print("MASS-STORAGE PERFORMANCE BENCHMARK")
        print("COSC 2667 Operating Systems Project")
        print("=" * 60)
        print(f"\nTest Directory: {self.test_dir.absolute()}")
        print(f"Test File Size: {TEST_FILE_SIZE_MB} MB")
        print(f"Iterations: {ITERATIONS}")
        print("-" * 60)
        
        results = {
            "sequential_write": {},
            "sequential_read": {},
            "random_read": {},
            "random_write": {},
            "metadata": {
                "test_file_size_mb": TEST_FILE_SIZE_MB,
                "iterations": ITERATIONS,
                "random_ops": RANDOM_OPS_COUNT
            }
        }
        
        for block_size in BLOCK_SIZES:
            bs_label = self._format_size(block_size)
            print(f"\n>>> Testing with Block Size: {bs_label}")
            
            # Sequential Write
            print(f"  Sequential Write...", end=" ", flush=True)
            write_speeds = []
            for _ in range(ITERATIONS):
                speed, _ = self.sequential_write_test(TEST_FILE_SIZE_MB, block_size)
                write_speeds.append(speed)
            avg_write = statistics.mean(write_speeds)
            results["sequential_write"][bs_label] = round(avg_write, 2)
            print(f"{avg_write:.2f} MB/s")
            
            # Sequential Read
            print(f"  Sequential Read...", end=" ", flush=True)
            read_speeds = []
            for _ in range(ITERATIONS):
                speed, _ = self.sequential_read_test(block_size)
                read_speeds.append(speed)
            avg_read = statistics.mean(read_speeds)
            results["sequential_read"][bs_label] = round(avg_read, 2)
            print(f"{avg_read:.2f} MB/s")
            
            # Random Read
            print(f"  Random Read...", end=" ", flush=True)
            iops_list = []
            latency_list = []
            for _ in range(ITERATIONS):
                iops, latency, _ = self.random_read_test(block_size, RANDOM_OPS_COUNT)
                iops_list.append(iops)
                latency_list.append(latency)
            avg_iops = statistics.mean(iops_list)
            avg_lat = statistics.mean(latency_list)
            results["random_read"][bs_label] = {
                "iops": round(avg_iops, 2),
                "latency_ms": round(avg_lat, 4)
            }
            print(f"{avg_iops:.2f} IOPS, {avg_lat:.4f} ms avg latency")
            
            # Random Write
            print(f"  Random Write...", end=" ", flush=True)
            iops_list = []
            latency_list = []
            for _ in range(ITERATIONS):
                iops, latency, _ = self.random_write_test(block_size, RANDOM_OPS_COUNT)
                iops_list.append(iops)
                latency_list.append(latency)
            avg_iops = statistics.mean(iops_list)
            avg_lat = statistics.mean(latency_list)
            results["random_write"][bs_label] = {
                "iops": round(avg_iops, 2),
                "latency_ms": round(avg_lat, 4)
            }
            print(f"{avg_iops:.2f} IOPS, {avg_lat:.4f} ms avg latency")
        
        # Cleanup
        self._cleanup()
        
        # Save results
        results_file = self.test_dir / "benchmark_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n[Results saved to {results_file}]")
        
        self._print_summary(results)
        return results
    
    def _format_size(self, size_bytes):
        """Format bytes to human readable"""
        if size_bytes >= 1048576:
            return f"{size_bytes // 1048576}MB"
        elif size_bytes >= 1024:
            return f"{size_bytes // 1024}KB"
        return f"{size_bytes}B"
    
    def _cleanup(self):
        """Remove test files"""
        if self.test_file.exists():
            self.test_file.unlink()
    
    def _print_summary(self, results):
        """Print formatted summary table"""
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        
        print("\nSequential Performance (MB/s):")
        print("-" * 40)
        print(f"{'Block Size':<12} {'Write':<15} {'Read':<15}")
        print("-" * 40)
        for bs in results["sequential_write"]:
            write = results["sequential_write"][bs]
            read = results["sequential_read"][bs]
            print(f"{bs:<12} {write:<15.2f} {read:<15.2f}")
        
        print("\nRandom Performance (IOPS):")
        print("-" * 50)
        print(f"{'Block Size':<12} {'Read IOPS':<15} {'Write IOPS':<15}")
        print("-" * 50)
        for bs in results["random_read"]:
            read_iops = results["random_read"][bs]["iops"]
            write_iops = results["random_write"][bs]["iops"]
            print(f"{bs:<12} {read_iops:<15.2f} {write_iops:<15.2f}")
        
        print("\nRandom Latency (ms):")
        print("-" * 50)
        print(f"{'Block Size':<12} {'Read Lat':<15} {'Write Lat':<15}")
        print("-" * 50)
        for bs in results["random_read"]:
            read_lat = results["random_read"][bs]["latency_ms"]
            write_lat = results["random_write"][bs]["latency_ms"]
            print(f"{bs:<12} {read_lat:<15.4f} {write_lat:<15.4f}")


# Simulated comparison data (HDD vs SSD typical values)
# Used for report generation when actual hardware isn't available
SIMULATED_HDD_DATA = {
    "sequential_write": {"4KB": 95.5, "16KB": 110.2, "64KB": 125.8, "256KB": 140.3, "1MB": 155.7},
    "sequential_read": {"4KB": 105.2, "16KB": 122.4, "64KB": 145.6, "256KB": 165.3, "1MB": 180.5},
    "random_read": {
        "4KB": {"iops": 85.3, "latency_ms": 11.72},
        "16KB": {"iops": 78.5, "latency_ms": 12.74},
        "64KB": {"iops": 65.2, "latency_ms": 15.34},
        "256KB": {"iops": 45.8, "latency_ms": 21.83},
        "1MB": {"iops": 28.4, "latency_ms": 35.21}
    },
    "random_write": {
        "4KB": {"iops": 75.6, "latency_ms": 13.23},
        "16KB": {"iops": 68.9, "latency_ms": 14.51},
        "64KB": {"iops": 55.3, "latency_ms": 18.08},
        "256KB": {"iops": 38.7, "latency_ms": 25.84},
        "1MB": {"iops": 22.1, "latency_ms": 45.25}
    }
}

SIMULATED_SSD_DATA = {
    "sequential_write": {"4KB": 485.3, "16KB": 510.7, "64KB": 535.2, "256KB": 548.9, "1MB": 555.4},
    "sequential_read": {"4KB": 520.6, "16KB": 545.8, "64KB": 558.3, "256KB": 565.1, "1MB": 570.2},
    "random_read": {
        "4KB": {"iops": 95000.5, "latency_ms": 0.0105},
        "16KB": {"iops": 75000.3, "latency_ms": 0.0133},
        "64KB": {"iops": 45000.8, "latency_ms": 0.0222},
        "256KB": {"iops": 18000.2, "latency_ms": 0.0556},
        "1MB": {"iops": 5500.6, "latency_ms": 0.1818}
    },
    "random_write": {
        "4KB": {"iops": 85000.2, "latency_ms": 0.0118},
        "16KB": {"iops": 68000.5, "latency_ms": 0.0147},
        "64KB": {"iops": 38000.3, "latency_ms": 0.0263},
        "256KB": {"iops": 15000.8, "latency_ms": 0.0667},
        "1MB": {"iops": 4800.4, "latency_ms": 0.2083}
    }
}


def generate_comparison_report():
    """Generate comparison data for report"""
    print("\n" + "=" * 70)
    print("HDD vs SSD PERFORMANCE COMPARISON")
    print("(Based on typical consumer-grade devices)")
    print("=" * 70)
    
    print("\n[1] SEQUENTIAL PERFORMANCE COMPARISON (MB/s)")
    print("-" * 60)
    print(f"{'Block Size':<12} {'HDD Write':<12} {'SSD Write':<12} {'Speedup':<10}")
    print("-" * 60)
    for bs in SIMULATED_HDD_DATA["sequential_write"]:
        hdd = SIMULATED_HDD_DATA["sequential_write"][bs]
        ssd = SIMULATED_SSD_DATA["sequential_write"][bs]
        speedup = ssd / hdd
        print(f"{bs:<12} {hdd:<12.1f} {ssd:<12.1f} {speedup:.1f}x")
    
    print("\n[2] RANDOM READ IOPS COMPARISON")
    print("-" * 60)
    print(f"{'Block Size':<12} {'HDD IOPS':<15} {'SSD IOPS':<15} {'Speedup':<10}")
    print("-" * 60)
    for bs in SIMULATED_HDD_DATA["random_read"]:
        hdd = SIMULATED_HDD_DATA["random_read"][bs]["iops"]
        ssd = SIMULATED_SSD_DATA["random_read"][bs]["iops"]
        speedup = ssd / hdd
        print(f"{bs:<12} {hdd:<15.1f} {ssd:<15.1f} {speedup:.0f}x")
    
    print("\n[3] RANDOM READ LATENCY COMPARISON (ms)")
    print("-" * 60)
    print(f"{'Block Size':<12} {'HDD Latency':<15} {'SSD Latency':<15} {'Reduction':<10}")
    print("-" * 60)
    for bs in SIMULATED_HDD_DATA["random_read"]:
        hdd = SIMULATED_HDD_DATA["random_read"][bs]["latency_ms"]
        ssd = SIMULATED_SSD_DATA["random_read"][bs]["latency_ms"]
        reduction = hdd / ssd
        print(f"{bs:<12} {hdd:<15.4f} {ssd:<15.4f} {reduction:.0f}x faster")
    
    print("\n" + "=" * 70)
    print("KEY FINDINGS:")
    print("-" * 70)
    print("• SSD sequential write is ~3.5x faster than HDD")
    print("• SSD random read IOPS is ~1000x higher than HDD")
    print("• SSD latency is ~1000x lower than HDD for random operations")
    print("• The gap widens significantly for small block random I/O")
    print("=" * 70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--compare":
        generate_comparison_report()
    else:
        test_dir = sys.argv[1] if len(sys.argv) > 1 else "./benchmark_test"
        benchmark = StorageBenchmark(test_dir)
        benchmark.run_full_benchmark()
