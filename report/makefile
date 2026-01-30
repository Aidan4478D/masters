TEX=src/main.tex
OUTDIR=build

.PHONY: all pdf clean

all: pdf

pdf:
	mkdir -p $(OUTDIR)
	latexmk -pdf -pvc -outdir=$(OUTDIR) $(TEX)

clean:
	latexmk -C -outdir=$(OUTDIR)
	rm -rf $(OUTDIR)

