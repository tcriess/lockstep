# Lockstep example demos -- build the .TOS intros and their STrinkler-packed variants.
#
# Unlike the hand-written aurora.s project (which assembles with vasm), each example here is a
# self-contained Python *emitter*: running it assembles and writes its .TOS in place (via
# lockstep.program.build_tos). So the build rule for every example is simply "run the script".
#
#   make               build all example .TOS                                   (default)
#   make aurora        build just examples/aurora/aurora.tos (the capstone)
#   make compressed    STrinkler-pack each .TOS into a *c.tos self-depacking exe
#   make clean         remove the compressed packs + generated intermediates
#
# Modeled on ~/development/atari/aurora/Makefile (the *c.tos / `STrinkler -9 -v` convention).
# NB: STrinkler is built for 4KiB demos -- `-9` on a large build takes minutes. Drop to e.g. -4
# to iterate.

PYTHON      := python3
STRINKLER   := STrinkler
STRINKFLAGS := -9 -v

# Lockstep toolkit sources: touch any of these and every example rebuilds.
TOOLKIT := $(wildcard lockstep/*.py) $(wildcard st68k/*.py)

# Each example -> the .TOS it emits.
AURORA   := examples/aurora/aurora.tos
DEMO     := examples/aurora/demo.tos
BORDOPEN := examples/bordopen/bordopen.tos
BORDWS   := examples/bordopen/bordws.tos

EXAMPLES   := $(AURORA) $(DEMO) $(BORDOPEN) $(BORDWS)
COMPRESSED := $(EXAMPLES:.tos=c.tos)

.PHONY: all compressed clean aurora demo bordopen docs docs-deps docs-serve docs-figures
all: $(EXAMPLES)
compressed: $(COMPRESSED)

# convenience aliases
aurora:   $(AURORA)
demo:     $(DEMO)
bordopen: $(BORDOPEN) $(BORDWS)

# --- example build rules (the emitter writes the .TOS as a side effect of running it) ---
# aurora.py rebuilds the demo from examples/aurora/orig/*.s: it re-derives every cycle count the
# original's author wrote by hand, so it depends on those sources too.
$(AURORA): examples/aurora/aurora.py $(wildcard examples/aurora/orig/*.s) $(TOOLKIT)
	$(PYTHON) $<

# demo.py also writes demo.s and runs a SANDBOXED (dummy-video) Hatari boot-check -- slow but harmless.
$(DEMO): examples/aurora/demo.py $(TOOLKIT)
	$(PYTHON) $<

# bordopen.py emits BOTH bordopen.tos and bordws.tos in a single run (grouped target, GNU make >=4.3).
$(BORDOPEN) $(BORDWS) &: examples/bordopen/bordopen.py $(TOOLKIT)
	$(PYTHON) $<

# --- STrinkler-compressed, self-depacking executables (one per .TOS) ---
%c.tos: %.tos
	$(STRINKLER) $(STRINKFLAGS) $< $@

# --- Documentation site (mkdocs.yml -> site/, published to GitHub Pages by .github/workflows) ---
#   make docs-serve     live preview on http://127.0.0.1:8000
#   make docs           build site/ exactly as CI does (--strict: broken links fail)
#   make docs-figures   re-shoot the devlog's Hatari screenshots (needs hatari + a TOS ROM)
docs-deps:
	$(PYTHON) -m pip install -r requirements-docs.txt

docs-serve:
	mkdocs serve

docs:
	mkdocs build --strict

docs-figures: $(EXAMPLES)
	$(PYTHON) docs/blog/posts/img/make_images.py

clean:
	rm -f $(COMPRESSED) examples/aurora/demo.s examples/aurora/demo.png
	rm -rf site
