from rdflib import Graph

from fair_workflow import __version__
from tests.dev import training_workflow


def test_api():
    """Test the package main function"""
    g = training_workflow._fair_workflow
    assert isinstance(g, Graph)
    assert len(g) > 10


def test_version():
    """Test the version is a string."""
    assert isinstance(__version__, str)
