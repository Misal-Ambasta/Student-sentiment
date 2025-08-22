#!/usr/bin/env python3
"""
Dynamic confidence score calculation for RAG responses
"""

import json
import re
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from loguru import logger

class ConfidenceCalculator:
    """Calculate dynamic confidence scores for RAG responses"""
    
    def __init__(self):
        self.min_confidence = 0.3
        self.max_confidence = 0.95
    
    def calculate_data_quality_score(self, documents: List[Document]) -> float:
        """Calculate data quality score based on document characteristics"""
        if not documents:
            return 0.1
        
        quality_factors = []
        
        # Document count factor (more documents = higher confidence)
        doc_count = len(documents)
        if doc_count >= 10:
            quality_factors.append(0.9)
        elif doc_count >= 5:
            quality_factors.append(0.7)
        elif doc_count >= 3:
            quality_factors.append(0.6)
        else:
            quality_factors.append(0.4)
        
        # Content richness factor
        total_content_length = 0
        for doc in documents:
            if hasattr(doc, 'page_content'):
                total_content_length += len(doc.page_content)
            elif isinstance(doc, dict) and 'content' in doc:
                total_content_length += len(doc['content'])
            else:
                total_content_length += len(str(doc))
        
        avg_content_length = total_content_length / doc_count
        
        if avg_content_length >= 200:
            quality_factors.append(0.8)
        elif avg_content_length >= 100:
            quality_factors.append(0.6)
        else:
            quality_factors.append(0.4)
        
        # Metadata completeness factor
        docs_with_metadata = 0
        for doc in documents:
            if hasattr(doc, 'metadata') and doc.metadata:
                docs_with_metadata += 1
            elif isinstance(doc, dict) and 'metadata' in doc and doc['metadata']:
                docs_with_metadata += 1
        
        metadata_ratio = docs_with_metadata / doc_count
        quality_factors.append(metadata_ratio * 0.8 + 0.2)
        
        # Document type diversity factor
        doc_types = set()
        for doc in documents:
            metadata = None
            if hasattr(doc, 'metadata'):
                metadata = doc.metadata
            elif isinstance(doc, dict) and 'metadata' in doc:
                metadata = doc['metadata']
            
            if metadata and 'document_type' in metadata:
                doc_types.add(metadata['document_type'])
        
        type_diversity = len(doc_types) / max(3, len(doc_types))  # Normalize to max 3 types
        quality_factors.append(min(type_diversity, 1.0) * 0.7 + 0.3)
        
        return sum(quality_factors) / len(quality_factors)
    
    def calculate_query_relevance_score(self, query: str, documents: List[Document]) -> float:
        """Calculate how relevant documents are to the query"""
        if not documents or not query:
            return 0.2
        
        query_words = set(query.lower().split())
        relevance_scores = []
        
        for doc in documents:
            # Handle both LangChain Document objects and dictionary formats
            if hasattr(doc, 'page_content'):
                content = doc.page_content
            elif isinstance(doc, dict) and 'content' in doc:
                content = doc['content']
            else:
                content = str(doc)
            
            content_words = set(content.lower().split())
            
            # Calculate word overlap
            overlap = len(query_words.intersection(content_words))
            overlap_ratio = overlap / len(query_words) if query_words else 0
            
            # Boost score if document contains key terms
            key_terms = ['nps', 'rating', 'score', 'feedback', 'course', 'student']
            key_term_matches = sum(1 for term in key_terms if term in content.lower())
            key_term_boost = min(key_term_matches * 0.1, 0.3)
            
            doc_relevance = min(overlap_ratio + key_term_boost, 1.0)
            relevance_scores.append(doc_relevance)
        
        return sum(relevance_scores) / len(relevance_scores)
    
    def calculate_response_completeness_score(self, response: str, analysis_type: str) -> float:
        """Calculate completeness score based on expected response structure"""
        if not response:
            return 0.1
        
        try:
            parsed_response = json.loads(response)
        except json.JSONDecodeError:
            return 0.3  # Lower confidence for non-JSON responses
        
        completeness_factors = []
        
        # Check for required fields
        required_fields = {
            'individual_analysis': ['type', 'content', 'student_id', 'risk_level'],
            'segmentation_analysis': ['type', 'content', 'segments'],
            'weekly_report': ['type', 'content', 'metadata']
        }
        
        expected_fields = required_fields.get(analysis_type, ['type', 'content'])
        present_fields = sum(1 for field in expected_fields if field in parsed_response)
        field_completeness = present_fields / len(expected_fields)
        completeness_factors.append(field_completeness)
        
        # Content richness analysis
        content = parsed_response.get('content', '')
        content_length = len(content)
        
        if content_length >= 500:
            completeness_factors.append(0.9)
        elif content_length >= 300:
            completeness_factors.append(0.7)
        elif content_length >= 150:
            completeness_factors.append(0.5)
        else:
            completeness_factors.append(0.3)
        
        # Check for specific analysis elements
        analysis_indicators = {
            'individual_analysis': ['NPS', 'Course A', 'Course B', 'CSBT', 'RECOMMENDED ACTIONS'],
            'segmentation_analysis': ['Working Professionals', 'Fresh Graduates', 'Career Switchers', 'TARGETED RECOMMENDATIONS'],
            'weekly_report': ['OVERALL METRICS', 'INSIGHTS', 'ANALYSIS']
        }
        
        expected_indicators = analysis_indicators.get(analysis_type, [])
        if expected_indicators:
            present_indicators = sum(1 for indicator in expected_indicators if indicator in content)
            indicator_completeness = present_indicators / len(expected_indicators)
            completeness_factors.append(indicator_completeness)
        
        return sum(completeness_factors) / len(completeness_factors)
    
    def calculate_historical_reliability_score(self, analysis_type: str, student_id: Optional[str] = None) -> float:
        """Calculate reliability score based on historical patterns and data availability"""
        # Base reliability scores for different analysis types
        base_reliability = {
            'individual_analysis': 0.75,  # Generally reliable with student-specific data
            'segmentation_analysis': 0.80,  # Good reliability with demographic data
            'weekly_report': 0.85,  # High reliability with comprehensive data
            'aspect_analysis': 0.70,  # Moderate reliability
            'general': 0.60  # Lower reliability for general queries
        }
        
        reliability = base_reliability.get(analysis_type, 0.60)
        
        # Boost confidence if we have specific student data
        if student_id and analysis_type == 'individual_analysis':
            reliability += 0.1
        
        # Adjust based on analysis complexity
        complexity_adjustments = {
            'segmentation_analysis': -0.05,  # Slightly more complex
            'weekly_report': 0.05,  # Well-established patterns
            'individual_analysis': 0.0  # Baseline
        }
        
        reliability += complexity_adjustments.get(analysis_type, 0)
        
        return min(max(reliability, 0.3), 0.9)
    
    def calculate_confidence(
        self,
        documents: List[Document],
        question: str,
        analysis_type: str,
        response: str = "",
        student_id: Optional[str] = None
    ) -> float:
        """Calculate confidence score for RAG responses (simplified interface)"""
        return self.calculate_confidence_score(
            query=question,
            documents=documents,
            response=response,
            analysis_type=analysis_type,
            student_id=student_id
        )
    
    def calculate_confidence_score(
        self,
        query: str,
        documents: List[Document],
        response: str,
        analysis_type: str,
        student_id: Optional[str] = None
    ) -> float:
        """Calculate overall confidence score combining multiple factors"""
        try:
            # Calculate individual scores
            data_quality = self.calculate_data_quality_score(documents)
            query_relevance = self.calculate_query_relevance_score(query, documents)
            response_completeness = self.calculate_response_completeness_score(response, analysis_type)
            historical_reliability = self.calculate_historical_reliability_score(analysis_type, student_id)
            
            # Weight the different factors
            weights = {
                'data_quality': 0.25,
                'query_relevance': 0.20,
                'response_completeness': 0.35,
                'historical_reliability': 0.20
            }
            
            # Calculate weighted average
            confidence = (
                data_quality * weights['data_quality'] +
                query_relevance * weights['query_relevance'] +
                response_completeness * weights['response_completeness'] +
                historical_reliability * weights['historical_reliability']
            )
            
            # Apply bounds and round to 2 decimal places
            confidence = max(self.min_confidence, min(confidence, self.max_confidence))
            confidence = round(confidence, 2)
            
            logger.info(f"Confidence calculation for {analysis_type}:")
            logger.info(f"  Data Quality: {data_quality:.2f}")
            logger.info(f"  Query Relevance: {query_relevance:.2f}")
            logger.info(f"  Response Completeness: {response_completeness:.2f}")
            logger.info(f"  Historical Reliability: {historical_reliability:.2f}")
            logger.info(f"  Final Confidence: {confidence:.2f}")
            
            return confidence
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5  # Return medium confidence as fallback
    
    def get_confidence_explanation(self, confidence: float) -> str:
        """Get human-readable explanation of confidence level"""
        if confidence >= 0.85:
            return "Very High - Comprehensive data with strong relevance"
        elif confidence >= 0.75:
            return "High - Good data quality and response completeness"
        elif confidence >= 0.65:
            return "Medium-High - Adequate data with some limitations"
        elif confidence >= 0.55:
            return "Medium - Moderate data quality or completeness"
        elif confidence >= 0.45:
            return "Medium-Low - Limited data or relevance issues"
        else:
            return "Low - Insufficient data or poor relevance"

# Global instance
confidence_calculator = ConfidenceCalculator()

def get_confidence_calculator() -> ConfidenceCalculator:
    """Get the global confidence calculator instance"""
    return confidence_calculator