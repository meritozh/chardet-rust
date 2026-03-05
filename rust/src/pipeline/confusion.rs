//! Confusion group resolution for similar single-byte encodings.

use super::DetectionResult;

/// Resolve confusion between similar encodings in the top results.
pub fn resolve_confusion_groups(
    _data: &[u8],
    results: Vec<DetectionResult>,
) -> Vec<DetectionResult> {
    // Simplified version - in the full implementation this would use
    // pre-computed distinguishing byte maps from confusion.bin
    
    if results.len() < 2 {
        return results;
    }
    
    // Check for known confusion pairs and resolve if needed
    let top = &results[0];
    let second = &results[1];
    
    if let (Some(ref enc1), Some(ref enc2)) = (&top.encoding, &second.encoding) {
        // Known confusion pairs
        let confusion_pairs: &[(&str, &str)] = &[
            ("iso-8859-1", "windows-1252"),
            ("iso-8859-2", "windows-1250"),
            ("iso-8859-5", "windows-1251"),
            ("iso-8859-6", "windows-1256"),
            ("iso-8859-7", "windows-1253"),
            ("iso-8859-8", "windows-1255"),
            ("iso-8859-9", "windows-1254"),
            ("iso-8859-13", "windows-1257"),
            ("koi8-r", "windows-1251"),
            ("mac-cyrillic", "windows-1251"),
        ];
        
        for (a, b) in confusion_pairs {
            if (enc1 == *a && enc2 == *b) || (enc1 == *b && enc2 == *a) {
                // Prefer Windows encodings over ISO equivalents
                let winner = if enc1.starts_with("windows-") { enc1 } else { enc2 };
                let loser = if enc1.starts_with("windows-") { enc2 } else { enc1 };
                
                if winner == enc2 {
                    // Swap results
                    let mut new_results = results.clone();
                    new_results.swap(0, 1);
                    return new_results;
                }
            }
        }
    }
    
    results
}
