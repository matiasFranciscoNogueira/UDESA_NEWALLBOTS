from enum import Enum


class SemanticChooserStrategy(Enum):
    """
    Enum for semantic chooser strategies.
    """
    
    BEST_PER_MODEL = "best_per_model"
    MEAN_SIMILARITY = "mean_similarity"
    CONSENSUS = "consensus"

    @classmethod
    def to_string(self):
        return self.value