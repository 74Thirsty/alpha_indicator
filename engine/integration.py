class ArbitragePathScorer:
    def __init__(self, model):
        self.model = model

    def score_paths(self, paths):
        """
        Accepts a list of path dicts, each with "features" key.
        Returns same list sorted by model score descending.
        """
        for path in paths:
            features = path.get("features")
            path["score"] = self.model.model.predict_proba([features])[0][1]
        return sorted(paths, key=lambda p: p["score"], reverse=True)