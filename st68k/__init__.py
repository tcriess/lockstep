"""st68k — cycle-exact cost model and tooling for Atari ST full-sync 68000 code.

See docs/DESIGN.md. The cost model is the foundation the scheduler (DESIGN §7) runs on.

Status: P1 — static cycle engine. The 68000 *nominal* timings (m68k_table) are the
well-documented part; the ST wait-state layer (cycles.WaitStateModel) currently ships
the first-order `round-up-to-4` approximation, to be replaced by the bus-phase model
once P0 (TIMING.md, mined from Hatari source) lands. See DESIGN §1.1.
"""

__all__ = ["parser", "m68k_table", "cycles", "annotate"]
