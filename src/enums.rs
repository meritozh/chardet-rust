//! Enumerations for chardet.

/// Bit flags representing encoding eras for filtering detection candidates.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum EncodingEra {
    /// Modern web encodings (UTF-8, Windows-1252, etc.)
    ModernWeb = 1,
    /// Legacy ISO encodings (ISO-8859-*, etc.)
    LegacyIso = 2,
    /// Legacy Mac encodings (MacRoman, etc.)
    LegacyMac = 4,
    /// Legacy regional encodings
    LegacyRegional = 8,
    /// DOS codepages (CP437, etc.)
    Dos = 16,
    /// Mainframe encodings (EBCDIC, etc.)
    Mainframe = 32,
    /// All encodings
    #[default]
    All = 63,
}

impl EncodingEra {
    /// Check if this era includes the given era flag.
    pub fn contains(&self, other: EncodingEra) -> bool {
        (*self as i32 & other as i32) != 0
    }
}

/// Language filter flags for UniversalDetector (chardet 6.x API compat).
///
/// Accepted but not used — the pipeline does not filter by language group.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
#[allow(non_camel_case_types)]
pub enum LanguageFilter {
    CHINESE_SIMPLIFIED = 0x01,
    CHINESE_TRADITIONAL = 0x02,
    JAPANESE = 0x04,
    KOREAN = 0x08,
    NON_CJK = 0x10,
    #[default]
    ALL = 0x1F,
    /// Chinese (simplified + traditional)
    CHINESE = 0x03,
    /// CJK (all Chinese, Japanese, Korean)
    CJK = 0x0F,
}