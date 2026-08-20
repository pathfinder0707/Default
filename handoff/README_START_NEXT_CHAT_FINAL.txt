Continue from this final GB-time tools handoff.

Files included:
- GB_FINAL_HANDOFF.md
- GB_FINAL_IMPLEMENTATION_NOTES.md
- gb-time-multi-swing-path-scorer-final.pine
- gb-confluence-fixed-reference.html

Current priority:
1. Compile-test gb-time-multi-swing-path-scorer-final.pine in TradingView Pine v6.
2. Fix any syntax issues without changing the core design.
3. Keep it as a multi-swing path scorer, not a global node scanner.
4. Preserve all three methods: MM, HH+MM, |HH-MM|, with MM primary.
5. Preserve Algo 2 reverse logic.

Main product direction:
- Use confirmed swing highs/lows only.
- Use multi-swing history internally to identify Algo 1 vs Algo 2.
- Show only recent swing-node labels, primary next line, alternate next line, and table.
- Avoid chart bloat.
