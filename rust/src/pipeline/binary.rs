//! Stage 0: Binary content detection.

/// Threshold: if more than this fraction of bytes are binary indicators, it's binary.
const BINARY_THRESHOLD: f64 = 0.01;

/// Check if data appears to be binary (not text) content.
pub fn is_binary(data: &[u8], max_bytes: usize) -> bool {
    let data = &data[..data.len().min(max_bytes)];
    if data.is_empty() {
        return false;
    }
    
    // Count binary-indicator control bytes (0x00-0x08, 0x0E-0x1F — excludes \t \n \v \f \r)
    let binary_count: usize = data
        .iter()
        .filter(|&&b| (b <= 0x08) || (b >= 0x0E && b <= 0x1F))
        .count();
    
    (binary_count as f64) / (data.len() as f64) > BINARY_THRESHOLD
}
