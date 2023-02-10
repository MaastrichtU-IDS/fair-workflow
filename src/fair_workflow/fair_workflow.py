import ast
import functools
import inspect

import matplotlib.pyplot as plt
import networkx as nx
import rdflib
from git import Repo
from rdflib import RDF, RDFS, Graph, Literal, URIRef
from yaml import dump

from fair_workflow.namespaces import DUL, NP, PPLAN, PWO


def extract_functions(source_code):
    """Extract functions used in a function"""
    func_meta = {
        "args": [],
        "returns": [],
        "func_calls": [],
    }

    parsed_code = ast.parse(source_code)

    for node in ast.walk(parsed_code):
        if isinstance(node, ast.FunctionDef):
            func_meta["name"] = node.name
            func_meta["args"] = ([arg.arg for arg in node.args.args],)
            func_meta["returns"] = [child.value.id for child in ast.walk(node) if isinstance(child, ast.Return)]

        if isinstance(node, ast.Assign):
            # Extract args
            args = {}
            if isinstance(node.value, ast.Call):
                for arg in node.value.keywords:
                    if isinstance(arg.value, ast.Name):
                        args[arg.arg] = arg.value.id
                    if isinstance(arg.value, ast.Constant):
                        args[arg.arg] = ast.literal_eval(arg.value)

            # Extract returns
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.Name):
                    assigned_vars = [child.id]
                if isinstance(child, ast.Tuple):
                    assigned_vars = []
                    # for tuple_value in child.dims:
                    #        assigned_vars.append(tuple_value.id)
                if isinstance(child, ast.Call):
                    function_name = child.func.id

                    # import importlib
                    # module = importlib.import_module(module_name)
                    # class_ = getattr(module, class_name)
                    # import sys
                    # print(dir(sys.modules[__name__]))
                    # current_module = globals()["__name__"]
                    # print(globals()["__name__"])
                    # print(inspect.getsource(function_name))

                    # print("CHILDISH")
                    # print(child)
                    # for childish in ast.iter_child_nodes(child):
                    #     if isinstance(childish, ast.Constant):
                    #         print(ast.literal_eval(childish))
                    #     elif isinstance(childish, ast.Name):
                    #         print(childish.id)
                    #     elif isinstance(childish, ast.keyword):
                    #         for arg_child in ast.iter_child_nodes(childish):
                    #             print(arg_child)
                    #     else:
                    #         print(childish)
                    # input_params = [arg.id for arg in node.args]

                    # for arg in child.args:
                    #     print("ARGS")
                    #     print(arg)
                    #     if isinstance(arg, ast.Constant):
                    #         print(ast.literal_eval(arg))
                    #     else:
                    #         print(arg.id)

                    func_meta["func_calls"].append({"name": function_name, "args": args, "returns": assigned_vars})

    return func_meta


def generate_rdf_triples(func_meta, namespace=NP):
    """Generate RDF from the extracted functions infos"""
    g = Graph()
    g.bind("pplan", PPLAN)
    g.bind("np", NP)
    g.bind("pwo", PWO)
    g.bind("dul", DUL)

    g.add((namespace[func_meta["name"]], RDF.type, PPLAN.Plan))
    g.add((namespace[func_meta["name"]], RDFS.label, Literal(func_meta["name"])))

    try:
        repo = Repo(".")
        git_url = repo.remotes.origin.url
    except:
        git_url = input("No URL to a remote git repository found, provide it please: ")
    g.add((namespace[func_meta["name"]], DUL.realizes, URIRef(git_url)))

    precedent_step = None
    for i, data in enumerate(func_meta["func_calls"]):
        func_uri = namespace[data["name"]]

        if i == 0:
            g.add((namespace[func_meta["name"]], PPLAN.hasFirstStep, func_uri))

        if precedent_step:
            g.add((precedent_step, DUL.precedes, func_uri))

        g.add((func_uri, RDF.type, PPLAN.Step))
        input_args = data["args"]
        if input_args:
            for i, arg in enumerate(input_args.items()):
                name = arg[0]
                value = arg[1]
                arg_uri = func_uri + "_" + name
                g.add((arg_uri, RDF.type, PPLAN.Variable))
                g.add((func_uri, PPLAN.hasInputVar, arg_uri))
                g.add((arg_uri, RDF.value, Literal(value)))
                g.add((arg_uri, RDFS.label, Literal(name)))
        assigned_vars = data["returns"]
        if assigned_vars:
            for i, var in enumerate(assigned_vars):
                var_uri = func_uri + "_" + var
                g.add((var_uri, rdflib.RDF.type, PPLAN.Variable))
                g.add((func_uri, PPLAN.isOutputVarOf, var_uri))
                g.add((var_uri, rdflib.RDF.value, Literal(var)))
        precedent_step = func_uri
    return g


def generate_visualization(g):
    """Generate networkx visualization from RDFLib Graph"""
    dg = nx.DiGraph()

    for subject, predicate, obj in g:
        subject = str(subject).replace("http://purl.org/nanopub/temp/np/", "")
        # predicate = str(predicate).replace("http://purl.org/nanopub/temp/np/", "")
        obj = str(obj).replace("http://purl.org/nanopub/temp/np/", "")
        if (
            str(predicate) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
            and str(obj) == "http://purl.org/net/p-plan#Step"
        ):
            # step_node = pydot.Node(subject, shape="box")
            # graph.add_node(step_node)
            dg.add_node(subject, size=100)
            # nx.draw_networkx_nodes(G, pos, node_size=600, node_color='w', alpha=0.4, node_shape='d')
        if (
            str(predicate) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
            and str(obj) == "http://purl.org/net/p-plan#Variable"
        ):
            dg.add_node(subject, size=1)

        elif str(predicate) == "http://purl.org/net/p-plan#hasInputVar":
            # input_var_node = pydot.Node(object, shape="ellipse")
            # graph.add_node(input_var_node)
            dg.add_edge(subject, obj)
        elif str(predicate) == "http://purl.org/net/p-plan#isOutputVarOf":
            # output_var_node = pydot.Node(object, shape="ellipse")
            # graph.add_node(output_var_node)
            # graph.add_edge(pydot.Edge(subject, output_var_node))
            dg.add_edge(subject, obj)

    # Plot Networkx instance of RDF Graph
    pos = nx.spring_layout(dg)
    nx.draw(dg, pos, node_color="skyblue", edge_color="gray", with_labels=True)
    # plt.show()
    return plt

    # pos = nx.spring_layout(G, scale=2)
    # edge_labels = nx.get_edge_attributes(G, 'r')
    # nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    # nx.draw(G, with_labels=True)

    # #if not in interactive mode for
    # plt.show()

    # graph = pydot.Dot(graph_type='digraph')

    # for subject, predicate, object in rdf_graph:
    #     if predicate == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" and object == "http://purl.org/net/p-plan#Step":
    #         step_node = pydot.Node(subject, shape="box")
    #         graph.add_node(step_node)
    #     elif predicate == "http://purl.org/net/p-plan#hasInputVar":
    #         input_var_node = pydot.Node(object, shape="ellipse")
    #         graph.add_node(input_var_node)
    #         graph.add_edge(pydot.Edge(input_var_node, subject))
    #     elif predicate == "http://purl.org/net/p-plan#isOutputVarOf":
    #         output_var_node = pydot.Node(object, shape="ellipse")
    #         graph.add_node(output_var_node)
    #         graph.add_edge(pydot.Edge(subject, output_var_node))

    # graph.write_png('rdf_graph.png')


def generate_cwl(g):
    cwl = {}
    return dump(cwl)


def generate_nexflow(g):
    """Generate Nextflow workflow from RDFLib Graph"""
    steps = {}

    var_dict = {}
    for s, p, o in g.triples((None, RDF["value"], None)):
        var = str(s).split("/")[-1]
        val = str(o).split("/")[-1]
        var_dict[var] = val
    print(var_dict)

    for s, p, o in g.triples((None, PPLAN["isOutputVarOf"], None)):
        step = str(s).split("/")[-1]
        var = str(o).split("/")[-1]
        if step not in steps:
            steps[step] = []
        steps[step].append(var)

    deps = {}
    for s, p, o in g.triples((None, DUL["precedes"], None)):
        step1 = str(s).split("/")[-1]
        step2 = str(o).split("/")[-1]
        if step2 not in deps:
            deps[step2] = []
        deps[step2].append(step1)

    # generate the Netflow description
    netflow_desc = ""
    for step in steps:
        netflow_desc += f"process {step} {{\n"
        netflow_desc += "  input:\n"
        for var in steps[step]:
            netflow_desc += f" file {var} from {var_dict[var]} \n"
        netflow_desc += "  output:\n"
        netflow_desc += f"    {var}: File\n"
        netflow_desc += "  script: ...\n"
        netflow_desc += "}}\n"

    for step1 in deps:
        for step2 in deps[step1]:
            netflow_desc += f"{step1} -> {step2}\n"

    print(netflow_desc)
    return netflow_desc


def fair_workflow(
    label: str,
):
    """A decorator to indicate a function is a fair workflow"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **qwargs):
            return func(*args, **qwargs)

        funcs = extract_functions(inspect.getsource(func))
        g = generate_rdf_triples(funcs)
        wrapper._fair_workflow = g
        wrapper._fair_workflow_visualization = generate_visualization(g)
        wrapper._fair_workflow_cwl = generate_nexflow(g)

        return wrapper

    return decorator
