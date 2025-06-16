from uuid import UUID

from poprox_storage.concepts.experiment import Experiment, Team, Treatment
from poprox_storage.concepts.manifest import manifest_to_experiment, parse_manifest_toml
from poprox_storage.paths import project_root


def test_load_manifest():
    with open(project_root() / "tests" / "data" / "sample_manifest.toml") as f:
        sample_manifest = f.read()
    manifest = parse_manifest_toml(sample_manifest)
    experiment = manifest_to_experiment(manifest)

    assert isinstance(experiment, Experiment)
    assert isinstance(experiment.experiment_id, UUID)
    assert isinstance(experiment.owner, Team)

    assert len(experiment.groups) == 3
    assert isinstance(experiment.groups[0].group_id, UUID)

    assert len(experiment.recommenders) == 3
    assert isinstance(experiment.recommenders[0].recommender_id, UUID)

    assert len(experiment.phases) == 3
    assert isinstance(experiment.phases[0].phase_id, UUID)

    # get phase 1 assignment a treatment
    assert len(experiment.phases[0].treatments) == 3
    targets = [treatment for treatment in experiment.phases[0].treatments if treatment.recommender.name == "x"]
    assert len(targets) == 1

    # assert the tempalte gets loaded
    assert isinstance(targets[0], Treatment)
    assert targets[0].template == "funkyTemplate.html"
