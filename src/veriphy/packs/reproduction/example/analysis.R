# The effect of a car's weight on its fuel use, in miles per gallon per 1000 lbs, as a linear regression.
run <- function(data, inputs) {
  formula <- if (nzchar(inputs$variation)) inputs$variation else "mpg ~ wt"
  coefficients <- summary(lm(as.formula(formula), data = data))$coefficients
  list(estimate = coefficients["wt", "Estimate"], se = coefficients["wt", "Std. Error"])
}
