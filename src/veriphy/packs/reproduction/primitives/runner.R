# Run an analysis script on its data: Rscript runner.R <script> <data> <seed> <out> <variation>
# The script defines run(data, inputs), returning list(estimate = ..., se = ...); the runner writes them as JSON.
args <- commandArgs(trailingOnly = TRUE)
set.seed(as.integer(args[3]))
source(args[1])
data <- read.csv(args[2])
variation <- paste(readLines(args[5], warn = FALSE), collapse = "\n")
result <- run(data, list(variation = variation))
writeLines(sprintf('{"status": "reported", "estimate": %.17g, "se": %.17g}', result$estimate, result$se), args[4])
