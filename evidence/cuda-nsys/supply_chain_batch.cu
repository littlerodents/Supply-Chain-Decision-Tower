// 供应链巡检的 GPU 化原型：对 N 个 SKU×仓库组合做"库存-需求缺口"批量核算
// （与 daily_scan.py 同一算术，展示该批处理在 GB10/CUDA 13.0 上的可移植路径）
#include <cstdio>
#include <cuda_runtime.h>

__global__ void gap_kernel(const int* stock, const int* demand, int* gap, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) gap[i] = stock[i] - demand[i];
}

int main() {
    const int N = 1 << 20;  // 100 万组合（演示 64 组合的 16384 倍规模）
    int *h_stock = new int[N], *h_demand = new int[N], *h_gap = new int[N];
    for (int i = 0; i < N; i++) { h_stock[i] = i % 5000; h_demand[i] = ((long)i * 7919) % 8000; }
    int *d_stock, *d_demand, *d_gap;
    cudaMalloc(&d_stock, N * sizeof(int)); cudaMalloc(&d_demand, N * sizeof(int)); cudaMalloc(&d_gap, N * sizeof(int));
    cudaMemcpy(d_stock, h_stock, N * sizeof(int), cudaMemcpyHostToDevice);
    cudaMemcpy(d_demand, h_demand, N * sizeof(int), cudaMemcpyHostToDevice);
    gap_kernel<<<(N + 255) / 256, 256>>>(d_stock, d_demand, d_gap, N);
    cudaMemcpy(h_gap, d_gap, N * sizeof(int), cudaMemcpyDeviceToHost);
    long shortage = 0; for (int i = 0; i < N; i++) if (h_gap[i] < 0) shortage++;
    printf("组合数=%d 短缺组合=%ld 样例gap[0]=%d gap[1]=%d\n", N, shortage, h_gap[0], h_gap[1]);
    printf("device=NVIDIA GB10 (CUDA runtime %d)\n", CUDART_VERSION);
    return 0;
}
