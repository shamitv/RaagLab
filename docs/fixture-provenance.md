# Original demo fixture provenance

`morning-spark`, revision `1`, is original text authored for MuseForge's Phase 2 implementation. It is embedded as `STATIC` in the lyrics provider and has not been copied from a song or external catalogue. The deterministic mock lyric template is also original, revision `1`. Static/mock text demonstrates source and persistence; language selections describe intent and do not promise translated demo output.

Music provider `mock`, revision `1`, synthesizes original sine-wave phrases and harmonics directly from a seeded note sequence. It uses no recording, sample library, model, paid endpoint, or weights. Identical effective seeds and durations in the same provider revision produce identical 44.1 kHz stereo 16-bit PCM output. Generated files carry measured metadata and SHA-256 in PostgreSQL. Cross-platform floating-point implementation differences are not a promise of bit-identical output across future runtimes.

Demo audio is instrumental. It does not sing the supplied lyrics or faithfully implement mood, genre, instrument, or language conditioning. User lyrics are labelled `user` and retained exactly; they are never represented as original static/mock content.
