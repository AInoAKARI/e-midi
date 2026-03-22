# E-MIDI Protocol Specification

E-MIDI is a fixed-length binary protocol for transporting emotional state as MIDI-compatible data.

## Message Layout

Each E-MIDI frame is exactly 23 bytes.

| Byte Offset | Length | Field | Description |
| --- | --- | --- | --- |
| 0 | 1 | header_0 | `0xE0` |
| 1 | 1 | header_1 | `0x4D` (`M`) |
| 2 | 1 | valence | `0-127` |
| 3 | 1 | arousal | `0-127` |
| 4 | 1 | tension | `0-127` |
| 5 | 1 | flags | `bit0=bounce`, `bit1-7=reserved` |
| 6 | 8 | source_id | ASCII sender ID, truncated/padded to 8 bytes |
| 14 | 8 | timestamp | Little-endian unsigned 64-bit integer, Unix time in milliseconds |
| 22 | 1 | reserved | Reserved for future compatibility, must be `0x00` |

## Encoding Rules

- `valence`, `arousal`, and `tension` must be clipped to the MIDI-safe range `0-127`.
- `flags & 0x01` indicates bounce detection.
- `source_id` accepts ASCII only. Longer values are truncated to 8 bytes. Shorter values are padded with `0x00`.
- `timestamp` is stored as `uint64` little-endian.
- Reserved byte must remain zero in version `0.1`.

## Example

```text
e0 4d 40 40 40 00 61 6b 61 72 69 00 00 00 15 cd 5b 07 00 00 00 00 00
```

This frame represents:

- `valence=64`
- `arousal=64`
- `tension=64`
- `bounce=false`
- `source_id="akari"`
- `timestamp=123456789`
