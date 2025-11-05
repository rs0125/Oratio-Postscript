"""
Similarity service for calculating vector similarity scores.
"""
from app.core.logging_config import get_logger
from typing import List, Optional, Tuple
import numpy as np
from scipy.spatial.distance import cosine

from app.core.exceptions import SimilarityError, ValidationError

logger = get_logger(__name__)


class SimilarityResult:
    """Container for similarity calculation results."""
    
    def __init__(self, score: float, normalized_score: float, interpretation: str):
        self.score = score
        self.normalized_score = normalized_score
        self.interpretation = interpretation


class SimilarityService:
    """Service for calculating similarity between text embeddings."""
    
    def __init__(self):
        """Initialize the similarity service."""
        pass
    
    def calculate_cosine_similarity(
        self, 
        vector1: List[float], 
        vector2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vector1: First embedding vector
            vector2: Second embedding vector
            
        Returns:
            Cosine similarity score between -1 and 1
            
        Raises:
            SimilarityValidationError: If vectors are invalid or incompatible
        """
        if not vector1 or not vector2:
            raise ValidationError("Vectors cannot be empty", field="vectors")
            
        if len(vector1) != len(vector2):
            raise ValidationError(
                f"Vector dimensions must match: {len(vector1)} vs {len(vector2)}",
                field="vector_dimensions",
                details={"vector1_dim": len(vector1), "vector2_dim": len(vector2)}
            )
            
        try:
            # Convert to numpy arrays
            arr1 = np.array(vector1, dtype=np.float64)
            arr2 = np.array(vector2, dtype=np.float64)
            
            # Check for zero vectors
            if np.allclose(arr1, 0) or np.allclose(arr2, 0):
                logger.warning("One or both vectors are zero vectors")
                return 0.0
                
            # Calculate cosine similarity (1 - cosine distance)
            similarity = 1 - cosine(arr1, arr2)
            
            # Handle potential numerical issues
            if np.isnan(similarity):
                logger.warning("Cosine similarity calculation resulted in NaN")
                return 0.0
                
            # Clamp to valid range [-1, 1]
            similarity = np.clip(similarity, -1.0, 1.0)
            
            logger.debug(f"Calculated cosine similarity: {similarity}")
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate cosine similarity: {str(e)}")
            raise SimilarityError(f"Similarity calculation error: {str(e)}") from e
    
    def normalize_similarity_score(self, cosine_score: float) -> float:
        """
        Normalize cosine similarity score to 0-1 range.
        
        Args:
            cosine_score: Cosine similarity score between -1 and 1
            
        Returns:
            Normalized score between 0 and 1
        """
        # Convert from [-1, 1] to [0, 1] range
        normalized = (cosine_score + 1.0) / 2.0
        return np.clip(normalized, 0.0, 1.0)
    
    def interpret_similarity_score(self, normalized_score: float) -> str:
        """
        Provide human-readable interpretation of similarity score.
        
        Args:
            normalized_score: Normalized similarity score between 0 and 1
            
        Returns:
            String interpretation of the similarity level
        """
        if normalized_score >= 0.9:
            return "Very High Similarity"
        elif normalized_score >= 0.8:
            return "High Similarity"
        elif normalized_score >= 0.7:
            return "Moderate-High Similarity"
        elif normalized_score >= 0.6:
            return "Moderate Similarity"
        elif normalized_score >= 0.5:
            return "Low-Moderate Similarity"
        elif normalized_score >= 0.3:
            return "Low Similarity"
        else:
            return "Very Low Similarity"
    
    def calculate_similarity(
        self, 
        vector1: List[float], 
        vector2: List[float]
    ) -> SimilarityResult:
        """
        Calculate complete similarity analysis between two vectors.
        
        Args:
            vector1: First embedding vector
            vector2: Second embedding vector
            
        Returns:
            SimilarityResult with score, normalized score, and interpretation
            
        Raises:
            SimilarityValidationError: If vectors are invalid
            SimilarityError: If calculation fails
        """
        # Calculate raw cosine similarity
        cosine_score = self.calculate_cosine_similarity(vector1, vector2)
        
        # Normalize to 0-1 range
        normalized_score = self.normalize_similarity_score(cosine_score)
        
        # Get interpretation
        interpretation = self.interpret_similarity_score(normalized_score)
        
        logger.debug(f"Similarity analysis - Raw: {cosine_score:.4f}, "
                    f"Normalized: {normalized_score:.4f}, "
                    f"Interpretation: {interpretation}")
        
        return SimilarityResult(
            score=cosine_score,
            normalized_score=normalized_score,
            interpretation=interpretation
        )
    
    def calculate_batch_similarities(
        self, 
        reference_vector: List[float], 
        comparison_vectors: List[List[float]]
    ) -> List[SimilarityResult]:
        """
        Calculate similarities between a reference vector and multiple comparison vectors.
        
        Args:
            reference_vector: Reference embedding vector
            comparison_vectors: List of vectors to compare against reference
            
        Returns:
            List of SimilarityResult objects
            
        Raises:
            SimilarityValidationError: If inputs are invalid
        """
        if not comparison_vectors:
            raise ValidationError("Comparison vectors list cannot be empty", field="comparison_vectors")
            
        results = []
        for i, comparison_vector in enumerate(comparison_vectors):
            try:
                result = self.calculate_similarity(reference_vector, comparison_vector)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to calculate similarity for vector {i}: {str(e)}")
                # Add a zero similarity result for failed calculations
                results.append(SimilarityResult(
                    score=0.0,
                    normalized_score=0.0,
                    interpretation="Calculation Failed"
                ))
                
        logger.debug(f"Calculated {len(results)} similarity scores")
        return results