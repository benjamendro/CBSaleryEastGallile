"""Shared loaders for the CBSaleryEastGallile reliability suite.

These helpers read the *real* project artefacts (the dashboard HTML, the report
Markdown, the unified CSVs, the Eshkol mapping workbook). Nothing here fabricates
data: a test that cannot reach its source must skip loudly, never pass quietly.
"""
