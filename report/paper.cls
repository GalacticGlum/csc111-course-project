%% paper.cls
% 
% A simple documentclass for research papers.

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{paper}

\LoadClass[10pt,twocolumn,letterpaper]{article}
% Layout configuration
\setlength{\columnsep}{0.55cm}
\usepackage[top=1.8cm, bottom=1.9cm, left=1.7cm, right=1.7cm]{geometry}
\frenchspacing
\setlength{\pdfpagewidth}{8.5in}
\setlength{\pdfpageheight}{11in}

% General packages
\RequirePackage{times}
\RequirePackage{graphicx}
\usepackage[utf8]{inputenc}

% Math packages
\RequirePackage{amsmath}
\RequirePackage{amssymb}
\RequirePackage{amsfonts}
\RequirePackage{mathtools}
\RequirePackage{bm}

% We define some basic math macros to simplify life!
\newcommand{\R}{\mathbb{R}}
\newcommand{\Q}{\mathbb{Q}}
\newcommand{\Z}{\mathbb{Z}}
\newcommand{\N}{\mathbb{N}}