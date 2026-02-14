TEX=main.tex
OUTDIR=../build

.PHONY: all pdf clean

all: pdf

pdf:
	mkdir -p build
	cd src && latexmk -pdf -pvc -outdir=$(OUTDIR) $(TEX)

clean:
	cd src && latexmk -C -outdir=$(OUTDIR)
	rm -rf build

