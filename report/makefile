OUTDIR=../build
MAIN=main.tex

.PHONY: all pdf clean

all: pdf

pdf:
	mkdir -p build
	cd src && latexmk -pdf -pvc -outdir=$(OUTDIR) $(MAIN)

clean:
	cd src && latexmk -C -outdir=$(OUTDIR)
	rm -rf build
