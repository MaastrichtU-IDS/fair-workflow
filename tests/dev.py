from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier

from fair_workflow import fair_workflow, generate_visualization


def load_data():
    data, y = load_iris(return_X_y=True, as_frame=True)
    return data, y


def fit_classifier(hyper_params, data, y):
    clf = RandomForestClassifier(
        n_jobs=hyper_params["n_jobs"],
        random_state=hyper_params["random_state"],
    )
    clf.fit(data, y)
    return clf


def evaluate(model):
    # Evaluate the quality of your model using custom metrics
    # cf. https://scikit-learn.org/stable/modules/model_evaluation.html
    return {
        "precision": 0.85,
        "recall": 0.80,
        "accuracy": 0.85,
        "roc_auc": 0.90,
        "f1": 0.75,
        "average_precision": 0.85,
    }


# @fair_step
def save_model(model, path, sample_data, scores, hyper_params):
    return {
        "model": model,
        "path": path,
        "sample_data": sample_data,
        "scores": scores,
        "hyper_params": hyper_params,
    }


@fair_workflow(label="Iris example workflow")
def training_workflow(n_jobs: int):
    hyper_params = {"n_jobs": n_jobs, "random_state": 42}

    x, y = load_data()

    model = fit_classifier(hyper_params=hyper_params, data=x, y=y)

    scores = evaluate(model=model)

    loaded_model = save_model(
        models=model,
        path="models/iris_example",
        sample_data=x,
        scores=scores,
        hyper_params=hyper_params,
    )
    return loaded_model


if __name__ == "__main__":
    training_workflow._fair_workflow.serialize(format="turtle")
    print(training_workflow._fair_workflow.serialize(format="turtle"))
    generate_visualization(training_workflow._fair_workflow).show()

    # model = training_workflow(n_jobs=2)
