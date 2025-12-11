"""Analyzer agent for feedback analysis on anonymized conversations.

This agent takes an anonymized conversation and its summary, then performs
detailed analysis to extract insights, identify patterns, and provide
actionable feedback.
"""

from google.adk.agents import Agent
import re
from typing import Dict, List, Any

# Jamf Software Domain Knowledge Base
JAMF_KNOWLEDGE = {
    "apple_platforms": {
        "macos_versions": ["Sonoma", "Ventura", "Monterey", "Big Sur", "Catalina", "Mojave"],
        "ios_versions": ["iOS 17", "iOS 16", "iOS 15", "iPadOS 17", "iPadOS 16"],
        "hardware_terms": ["Apple Silicon", "M1", "M2", "M3", "T2 Security Chip", "Secure Enclave", "Touch ID", "Face ID"],
        "system_features": ["System Integrity Protection", "Gatekeeper", "XProtect", "FileVault", "Secure Boot", "Activation Lock"]
    },
    "jamf_products": {
        "jamf_pro": ["Policy", "Configuration Profile", "Self Service", "Inventory Collection", "Computer Groups", "Smart Groups", "Prestage Enrollment"],
        "jamf_school": ["Classes", "App Assignment", "Restrictions", "Screen Time", "Student Progress", "Teacher Tools"],
        "jamf_connect": ["Password Sync", "Network Authentication", "Mobile Accounts", "Active Directory", "LDAP", "SSO"],
        "jamf_protect": ["Analytics", "Threat Events", "Computer Groups", "Compliance", "Endpoint Detection", "Unified Logs"]
    },
    "mdm_concepts": {
        "enrollment": ["DEP", "ADE", "User Initiated Enrollment", "Prestage Enrollment", "Manual Enrollment", "Zero-Touch"],
        "management": ["Configuration Profiles", "Restrictions", "Apps & Books", "Software Updates", "Remote Commands"],
        "security": ["FileVault Key Escrow", "Certificate Management", "VPN Configuration", "Wi-Fi Management", "Passcode Policies"]
    },
    "security_compliance": {
        "frameworks": ["Zero Trust", "NIST", "SOC2", "GDPR", "HIPAA", "CIS Controls"],
        "jamf_security": ["Jamf Protect", "Compliance Monitoring", "Threat Detection", "Endpoint Security"],
        "apple_security": ["System Integrity Protection", "Secure Boot", "Hardware Security", "App Notarization"]
    },
    "common_terms": {
        "deployment": ["Mass Deployment", "Imaging", "DEP Enrollment", "User Enrollment", "Device Enrollment"],
        "troubleshooting": ["Inventory Update", "Policy Execution", "Log Collection", "Remote Desktop", "Screen Sharing"],
        "integration": ["Active Directory", "LDAP", "SSO", "SCEP", "PKI", "API Integration"]
    }
}


def analyze_conversation_flow(messages: list[dict], summary: str) -> dict:
    """Analyze conversation flow patterns and interaction quality.

    Examines turn-taking, response patterns, topic progression, and
    conversation coherence using both raw messages and summary context.

    Args:
        messages: List of message dictionaries in history_message_schema format.
        summary: Structured summary from the summarizer agent.

    Returns:
        dict: Analysis results including flow metrics and quality indicators.
    """
    try:
        if not isinstance(messages, list):
            return {"status": "error", "error_message": "Messages must be a list"}

        if not messages:
            return {
                "status": "success",
                "flow_score": 0,
                "turn_taking_balance": 0,
                "topic_coherence": 0,
                "conversation_closure": 0,
                "patterns": []
            }

        # Analyze turn-taking patterns
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        total_messages = len(messages)
        if total_messages == 0:
            balance_score = 0
        else:
            user_ratio = len(user_messages) / total_messages
            # Optimal balance is around 40-60% user messages
            balance_score = max(0, 10 - abs(user_ratio - 0.5) * 20)

        # Analyze question-answer matching
        question_patterns = [r'\?', r'\bhow\b', r'\bwhat\b', r'\bwhy\b', r'\bwhen\b', r'\bwhere\b', r'\bcan you\b']
        question_count = 0

        for msg in user_messages:
            content = str(msg.get("content", "")).lower()
            for pattern in question_patterns:
                if re.search(pattern, content):
                    question_count += 1
                    break

        # Score based on assistant response availability
        response_coverage = min(10, (len(assistant_messages) / max(1, question_count)) * 10)

        # Analyze topic coherence from summary
        summary_lower = str(summary).lower()
        coherence_indicators = ["discussed", "addressed", "covered", "resolved", "explained"]
        coherence_signals = sum(1 for indicator in coherence_indicators if indicator in summary_lower)
        coherence_score = min(10, coherence_signals * 2)

        # Analyze conversation closure
        closure_indicators = ["resolved", "completed", "finished", "concluded", "helped"]
        closure_signals = sum(1 for indicator in closure_indicators if indicator in summary_lower)

        if messages and assistant_messages:
            last_message = messages[-1]
            if last_message.get("role") == "assistant":
                last_content = str(last_message.get("content", "")).lower()
                closure_phrases = ["help", "assist", "question", "need", "else"]
                has_closure_offer = any(phrase in last_content for phrase in closure_phrases)
                closure_score = min(10, closure_signals * 3 + (3 if has_closure_offer else 0))
            else:
                closure_score = max(0, closure_signals * 2)  # Lower score if user had last word
        else:
            closure_score = 0

        # Identify patterns
        patterns = []
        if balance_score < 5:
            if user_ratio < 0.3:
                patterns.append("conversation_dominated_by_assistant")
            else:
                patterns.append("conversation_dominated_by_user")

        if response_coverage < 7:
            patterns.append("inadequate_question_coverage")

        if coherence_score >= 8:
            patterns.append("strong_topic_coherence")
        elif coherence_score < 4:
            patterns.append("topic_drift_detected")

        # Calculate overall flow score
        flow_score = (balance_score + response_coverage + coherence_score + closure_score) / 4

        return {
            "status": "success",
            "flow_score": round(flow_score, 1),
            "turn_taking_balance": round(balance_score, 1),
            "question_response_coverage": round(response_coverage, 1),
            "topic_coherence": round(coherence_score, 1),
            "conversation_closure": round(closure_score, 1),
            "patterns": patterns,
            "metrics": {
                "total_messages": total_messages,
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "questions_identified": question_count,
                "user_message_ratio": round(user_ratio, 2)
            }
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Analysis failed: {str(e)}"}


def evaluate_response_quality(messages: list[dict], summary: str) -> dict:
    """Evaluate the quality and effectiveness of assistant responses.

    Analyzes response relevance, completeness, accuracy indicators,
    and helpfulness using conversation content and summary insights.

    Args:
        messages: List of message dictionaries in history_message_schema format.
        summary: Structured summary from the summarizer agent.

    Returns:
        dict: Response quality analysis with scores and indicators.
    """
    try:
        if not isinstance(messages, list):
            return {"status": "error", "error_message": "Messages must be a list"}

        assistant_messages = [m for m in messages if m.get("role") == "assistant"]
        user_messages = [m for m in messages if m.get("role") == "user"]

        if not assistant_messages:
            return {
                "status": "success",
                "quality_score": 0,
                "relevance_score": 0,
                "completeness_score": 0,
                "helpfulness_score": 0,
                "patterns": ["no_assistant_responses"]
            }

        # Analyze response relevance
        relevance_indicators = []
        for i, user_msg in enumerate(user_messages):
            user_content = str(user_msg.get("content", "")).lower()

            # Find corresponding assistant response
            assistant_response = None
            for j, assistant_msg in enumerate(assistant_messages):
                # Simple heuristic: assistant message after user message
                if j >= i:
                    assistant_response = assistant_msg
                    break

            if assistant_response:
                assistant_content = str(assistant_response.get("content", "")).lower()

                # Check for direct acknowledgment and addressing
                acknowledgment_phrases = ["understand", "see", "help", "answer", "address"]
                has_acknowledgment = any(phrase in assistant_content for phrase in acknowledgment_phrases)

                # Check for question words in user message and corresponding answers
                user_question_words = re.findall(r'\b(how|what|why|when|where|can|could|would|should)\b', user_content)
                if user_question_words and has_acknowledgment:
                    relevance_indicators.append(1)
                else:
                    relevance_indicators.append(0.5)

        relevance_score = (sum(relevance_indicators) / max(len(relevance_indicators), 1)) * 10

        # Analyze response completeness from summary
        summary_lower = str(summary).lower()
        completeness_indicators = ["addressed", "covered", "explained", "provided", "discussed", "resolved"]
        completeness_signals = sum(1 for indicator in completeness_indicators if indicator in summary_lower)
        completeness_score = min(10, completeness_signals * 1.5)

        # Analyze helpfulness patterns
        helpfulness_signals = 0
        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Look for examples and clarifications
            example_phrases = ["for example", "such as", "like", "instance", "consider"]
            if any(phrase in content for phrase in example_phrases):
                helpfulness_signals += 1

            # Look for proactive assistance
            proactive_phrases = ["also", "additionally", "furthermore", "might want", "consider", "suggest"]
            if any(phrase in content for phrase in proactive_phrases):
                helpfulness_signals += 1

            # Look for alternative solutions
            alternative_phrases = ["alternatively", "another way", "you could also", "option", "approach"]
            if any(phrase in content for phrase in alternative_phrases):
                helpfulness_signals += 1

        helpfulness_score = min(10, (helpfulness_signals / max(len(assistant_messages), 1)) * 10)

        # Analyze accuracy confidence indicators
        accuracy_indicators = []
        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # High confidence indicators
            high_confidence = ["definitely", "certainly", "absolutely", "exactly", "precisely"]
            medium_confidence = ["likely", "probably", "generally", "typically", "usually"]
            low_confidence = ["might", "could", "perhaps", "possibly", "may be"]

            if any(phrase in content for phrase in high_confidence):
                accuracy_indicators.append(1)
            elif any(phrase in content for phrase in medium_confidence):
                accuracy_indicators.append(0.8)
            elif any(phrase in content for phrase in low_confidence):
                accuracy_indicators.append(0.6)
            else:
                accuracy_indicators.append(0.7)  # Neutral

        accuracy_confidence = (sum(accuracy_indicators) / max(len(accuracy_indicators), 1)) * 10

        # Identify patterns
        patterns = []
        if relevance_score >= 8:
            patterns.append("highly_relevant_responses")
        elif relevance_score < 5:
            patterns.append("relevance_issues_detected")

        if helpfulness_score >= 7:
            patterns.append("proactive_helpfulness")
        elif helpfulness_score < 4:
            patterns.append("minimal_helpfulness")

        if completeness_score >= 8:
            patterns.append("comprehensive_coverage")
        elif completeness_score < 5:
            patterns.append("incomplete_responses")

        # Calculate overall quality score
        quality_score = (relevance_score + completeness_score + helpfulness_score + accuracy_confidence) / 4

        return {
            "status": "success",
            "quality_score": round(quality_score, 1),
            "relevance_score": round(relevance_score, 1),
            "completeness_score": round(completeness_score, 1),
            "helpfulness_score": round(helpfulness_score, 1),
            "accuracy_confidence": round(accuracy_confidence, 1),
            "patterns": patterns,
            "metrics": {
                "assistant_messages_analyzed": len(assistant_messages),
                "relevance_indicators": len(relevance_indicators),
                "helpfulness_signals": helpfulness_signals,
                "completeness_signals": completeness_signals
            }
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Response quality analysis failed: {str(e)}"}


def assess_communication_effectiveness(messages: list[dict], summary: str) -> dict:
    """Assess communication clarity, tone, and professionalism.

    Evaluates language clarity, tone consistency, empathy indicators,
    and professional communication standards.

    Args:
        messages: List of message dictionaries in history_message_schema format.
        summary: Structured summary from the summarizer agent.

    Returns:
        dict: Communication effectiveness analysis with scores and patterns.
    """
    try:
        if not isinstance(messages, list):
            return {"status": "error", "error_message": "Messages must be a list"}

        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        if not assistant_messages:
            return {
                "status": "success",
                "communication_score": 0,
                "clarity_score": 0,
                "tone_score": 0,
                "empathy_score": 0,
                "professionalism_score": 0,
                "patterns": ["no_assistant_messages"]
            }

        # Analyze language clarity
        clarity_signals = 0
        complexity_indicators = 0
        total_words = 0

        for msg in assistant_messages:
            content = str(msg.get("content", ""))
            words = content.split()
            total_words += len(words)

            # Clear language indicators
            clear_phrases = ["let me explain", "in other words", "to clarify", "simply put", "basically"]
            if any(phrase in content.lower() for phrase in clear_phrases):
                clarity_signals += 1

            # Complexity indicators (potential issues)
            complex_words = [word for word in words if len(word) > 12]
            if len(complex_words) > len(words) * 0.1:  # More than 10% complex words
                complexity_indicators += 1

        avg_words_per_message = total_words / max(len(assistant_messages), 1)
        clarity_score = max(0, min(10,
            (clarity_signals * 2) +
            (5 if avg_words_per_message < 100 else 3) -  # Conciseness bonus
            (complexity_indicators * 1.5)
        ))

        # Analyze tone consistency and appropriateness
        positive_tone_indicators = ["happy", "glad", "pleased", "excellent", "great", "wonderful"]
        empathetic_tone_indicators = ["understand", "appreciate", "sorry", "apologize", "concern"]
        professional_tone_indicators = ["recommend", "suggest", "advise", "consider", "propose"]

        tone_signals = 0
        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Look for appropriate tone markers
            if any(phrase in content for phrase in positive_tone_indicators):
                tone_signals += 1
            if any(phrase in content for phrase in empathetic_tone_indicators):
                tone_signals += 1
            if any(phrase in content for phrase in professional_tone_indicators):
                tone_signals += 1

        tone_score = min(10, (tone_signals / max(len(assistant_messages), 1)) * 5)

        # Analyze empathy indicators
        empathy_phrases = [
            "understand how you feel", "i can see why", "that must be frustrating",
            "i appreciate", "thank you for", "i'm sorry", "let me help",
            "i realize", "i recognize", "that sounds"
        ]

        empathy_signals = 0
        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()
            empathy_signals += sum(1 for phrase in empathy_phrases if phrase in content)

        empathy_score = min(10, empathy_signals * 2)

        # Analyze professionalism
        professional_elements = 0
        unprofessional_indicators = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Professional language markers
            professional_markers = ["please", "thank you", "would you", "could you", "if you'd like"]
            professional_elements += sum(1 for marker in professional_markers if marker in content)

            # Unprofessional indicators
            informal_language = ["gonna", "wanna", "yeah", "ok", "yep", "nope"]
            unprofessional_indicators += sum(1 for informal in informal_language if informal in content)

        professionalism_score = min(10, max(0,
            (professional_elements * 1.5) -
            (unprofessional_indicators * 2) + 5  # Base score
        ))

        # Analyze from summary context
        summary_lower = str(summary).lower()
        summary_communication_indicators = [
            "clearly explained", "well communicated", "professional manner",
            "empathetic response", "clear guidance", "helpful tone"
        ]
        summary_signals = sum(1 for indicator in summary_communication_indicators if indicator in summary_lower)

        # Adjust scores based on summary insights
        if summary_signals > 0:
            clarity_score = min(10, clarity_score + summary_signals * 0.5)
            tone_score = min(10, tone_score + summary_signals * 0.5)

        # Identify communication patterns
        patterns = []
        if clarity_score >= 8:
            patterns.append("excellent_clarity")
        elif clarity_score < 5:
            patterns.append("clarity_issues")

        if tone_score >= 7:
            patterns.append("appropriate_tone")
        elif tone_score < 4:
            patterns.append("tone_improvement_needed")

        if empathy_score >= 6:
            patterns.append("empathetic_communication")
        elif empathy_score < 3:
            patterns.append("lacks_empathy_indicators")

        if professionalism_score >= 8:
            patterns.append("highly_professional")
        elif professionalism_score < 5:
            patterns.append("professionalism_concerns")

        if avg_words_per_message > 200:
            patterns.append("verbose_responses")
        elif avg_words_per_message < 20:
            patterns.append("overly_brief_responses")

        # Calculate overall communication score
        communication_score = (clarity_score + tone_score + empathy_score + professionalism_score) / 4

        return {
            "status": "success",
            "communication_score": round(communication_score, 1),
            "clarity_score": round(clarity_score, 1),
            "tone_score": round(tone_score, 1),
            "empathy_score": round(empathy_score, 1),
            "professionalism_score": round(professionalism_score, 1),
            "patterns": patterns,
            "metrics": {
                "average_words_per_message": round(avg_words_per_message, 1),
                "clarity_signals": clarity_signals,
                "complexity_indicators": complexity_indicators,
                "tone_signals": tone_signals,
                "empathy_signals": empathy_signals,
                "professional_elements": professional_elements,
                "unprofessional_indicators": unprofessional_indicators,
                "summary_communication_signals": summary_signals
            }
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Communication assessment failed: {str(e)}"}


def analyze_technical_accuracy_indicators(messages: list[dict], summary: str) -> dict:
    """Analyze indicators of technical accuracy and reliability.

    Identifies confidence signals, verification patterns, and
    accuracy indicators in technical discussions.

    Args:
        messages: List of message dictionaries in history_message_schema format.
        summary: Structured summary from the summarizer agent.

    Returns:
        dict: Technical accuracy analysis with confidence scores and patterns.
    """
    try:
        if not isinstance(messages, list):
            return {"status": "error", "error_message": "Messages must be a list"}

        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        if not assistant_messages:
            return {
                "status": "success",
                "accuracy_score": 0,
                "confidence_handling": 0,
                "verification_score": 0,
                "uncertainty_management": 0,
                "patterns": ["no_assistant_messages"]
            }

        # Analyze confidence language patterns
        high_confidence_phrases = [
            "definitely", "certainly", "absolutely", "exactly", "precisely",
            "always", "never", "guaranteed", "without doubt", "确保", "must be"
        ]

        medium_confidence_phrases = [
            "likely", "probably", "generally", "typically", "usually",
            "often", "commonly", "tends to", "in most cases", "should be"
        ]

        uncertainty_phrases = [
            "might", "could", "perhaps", "possibly", "may be", "potentially",
            "i think", "i believe", "it seems", "appears to", "suggests",
            "not sure", "uncertain", "unclear"
        ]

        confidence_scores = []
        uncertainty_handling_signals = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Score confidence appropriateness
            high_conf_count = sum(1 for phrase in high_confidence_phrases if phrase in content)
            medium_conf_count = sum(1 for phrase in medium_confidence_phrases if phrase in content)
            uncertain_count = sum(1 for phrase in uncertainty_phrases if phrase in content)

            # Balanced confidence is better than extremes
            if high_conf_count > 0 and uncertain_count > 0:
                # Good: shows both confidence and appropriate uncertainty
                confidence_scores.append(8)
            elif medium_conf_count > 0:
                # Good: moderate confidence
                confidence_scores.append(7)
            elif uncertain_count > 0 and high_conf_count == 0:
                # Good: appropriate uncertainty without overconfidence
                confidence_scores.append(6)
            elif high_conf_count > uncertain_count and high_conf_count > 2:
                # Concerning: too much overconfidence
                confidence_scores.append(3)
            else:
                # Neutral: no clear indicators
                confidence_scores.append(5)

            # Check for uncertainty handling
            uncertainty_handling_phrases = [
                "let me verify", "i'll double check", "let me confirm",
                "according to", "based on", "as per", "documented",
                "i should clarify", "to be accurate"
            ]

            if any(phrase in content for phrase in uncertainty_handling_phrases):
                uncertainty_handling_signals += 1

        avg_confidence_score = sum(confidence_scores) / max(len(confidence_scores), 1)

        # Analyze verification and source patterns
        verification_indicators = [
            "according to", "based on", "documented", "official", "specification",
            "reference", "source", "documentation", "manual", "guide",
            "as stated in", "per the", "verified", "confirmed"
        ]

        correction_indicators = [
            "actually", "correction", "i misstated", "let me correct",
            "i was wrong", "mistake", "error", "incorrect", "revise"
        ]

        verification_signals = 0
        correction_signals = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            verification_signals += sum(1 for indicator in verification_indicators if indicator in content)
            correction_signals += sum(1 for indicator in correction_indicators if indicator in content)

        # Verification score (higher is better)
        verification_score = min(10, verification_signals * 2)

        # Correction handling (some corrections are good, too many indicate problems)
        if correction_signals == 0:
            correction_handling = 5  # Neutral - no corrections needed/made
        elif correction_signals <= 2:
            correction_handling = 8  # Good - appropriate corrections
        else:
            correction_handling = 3  # Concerning - many corrections needed

        # Analyze uncertainty management
        uncertainty_management_score = min(10,
            (uncertainty_handling_signals * 3) +
            (4 if any(s >= 6 for s in confidence_scores) else 2)
        )

        # Analyze technical depth appropriateness from summary
        summary_lower = str(summary).lower()
        technical_appropriateness_indicators = [
            "technical details", "appropriate level", "well explained",
            "clear technical", "accurate information", "proper guidance"
        ]

        summary_technical_signals = sum(1 for indicator in technical_appropriateness_indicators
                                      if indicator in summary_lower)

        # Adjust scores based on summary
        if summary_technical_signals > 0:
            verification_score = min(10, verification_score + summary_technical_signals)

        # Identify patterns
        patterns = []

        if avg_confidence_score >= 7:
            patterns.append("balanced_confidence_levels")
        elif avg_confidence_score <= 4:
            patterns.append("confidence_calibration_issues")

        if verification_score >= 6:
            patterns.append("good_source_verification")
        elif verification_score <= 2:
            patterns.append("lacks_source_verification")

        if uncertainty_management_score >= 7:
            patterns.append("excellent_uncertainty_handling")
        elif uncertainty_management_score <= 4:
            patterns.append("poor_uncertainty_management")

        if correction_signals > 0:
            patterns.append("self_correction_present")

        # Check for overconfidence pattern
        overconfident_messages = sum(1 for score in confidence_scores if score <= 3)
        if overconfident_messages > len(confidence_scores) * 0.3:
            patterns.append("overconfidence_detected")

        # Calculate overall accuracy score
        accuracy_score = (avg_confidence_score + verification_score +
                         uncertainty_management_score + correction_handling) / 4

        return {
            "status": "success",
            "accuracy_score": round(accuracy_score, 1),
            "confidence_handling": round(avg_confidence_score, 1),
            "verification_score": round(verification_score, 1),
            "uncertainty_management": round(uncertainty_management_score, 1),
            "correction_handling": round(correction_handling, 1),
            "patterns": patterns,
            "metrics": {
                "messages_analyzed": len(assistant_messages),
                "verification_signals": verification_signals,
                "correction_signals": correction_signals,
                "uncertainty_handling_signals": uncertainty_handling_signals,
                "avg_confidence_score": round(avg_confidence_score, 2),
                "overconfident_messages": overconfident_messages,
                "summary_technical_signals": summary_technical_signals
            }
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Technical accuracy analysis failed: {str(e)}"}


def evaluate_efficiency_metrics(messages: list[dict], summary: str) -> dict:
    """Evaluate conversation efficiency and resolution patterns.

    Analyzes how efficiently issues were resolved and conversations
    were conducted.

    Args:
        messages: List of message dictionaries in history_message_schema format.
        summary: Structured summary from the summarizer agent.

    Returns:
        dict: Efficiency analysis with directness and resolution metrics.
    """
    try:
        if not isinstance(messages, list):
            return {"status": "error", "error_message": "Messages must be a list"}

        assistant_messages = [m for m in messages if m.get("role") == "assistant"]
        user_messages = [m for m in messages if m.get("role") == "user"]

        if not assistant_messages:
            return {
                "status": "success",
                "efficiency_score": 0,
                "directness_score": 0,
                "resolution_score": 0,
                "conciseness_score": 0,
                "patterns": ["no_assistant_messages"]
            }

        # Analyze response directness
        directness_indicators = []
        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Direct response indicators
            direct_phrases = [
                "here's how", "the answer is", "simply", "directly",
                "to solve this", "the solution", "here's what you need"
            ]

            # Indirect/verbose indicators
            indirect_phrases = [
                "well, first", "let me start by explaining", "there are many ways",
                "it's complicated", "this is complex", "there are several factors"
            ]

            direct_count = sum(1 for phrase in direct_phrases if phrase in content)
            indirect_count = sum(1 for phrase in indirect_phrases if phrase in content)

            # Score directness (higher is more direct)
            if direct_count > indirect_count:
                directness_indicators.append(8)
            elif direct_count == indirect_count:
                directness_indicators.append(6)
            else:
                directness_indicators.append(4)

        directness_score = sum(directness_indicators) / max(len(directness_indicators), 1)

        # Analyze conciseness
        total_words = 0
        for msg in assistant_messages:
            content = str(msg.get("content", ""))
            total_words += len(content.split())

        avg_response_length = total_words / max(len(assistant_messages), 1)

        # Score conciseness (optimal range: 30-150 words per response)
        if 30 <= avg_response_length <= 150:
            conciseness_score = 10
        elif 150 < avg_response_length <= 200:
            conciseness_score = 8
        elif 200 < avg_response_length <= 300:
            conciseness_score = 6
        elif avg_response_length < 30:
            conciseness_score = 5  # Too brief might miss important info
        else:
            conciseness_score = 3  # Too verbose

        # Analyze redundancy
        redundancy_indicators = []
        for i, msg in enumerate(assistant_messages):
            content = str(msg.get("content", "")).lower()

            # Check for repetitive phrases within the same message
            words = content.split()
            redundancy_score = 0

            # Look for repeated phrases
            phrases_used = {}
            for j in range(len(words) - 1):
                phrase = f"{words[j]} {words[j+1]}"
                if phrase in phrases_used:
                    redundancy_score += 1
                else:
                    phrases_used[phrase] = 1

            # Penalize high redundancy
            if redundancy_score > len(words) * 0.1:  # More than 10% redundant phrases
                redundancy_indicators.append(3)
            elif redundancy_score > len(words) * 0.05:  # 5-10% redundant
                redundancy_indicators.append(6)
            else:
                redundancy_indicators.append(8)

        redundancy_score = sum(redundancy_indicators) / max(len(redundancy_indicators), 1)

        # Analyze resolution effectiveness from summary
        summary_lower = str(summary).lower()
        resolution_indicators = [
            "resolved", "solved", "completed", "addressed", "answered",
            "clarified", "explained", "helped", "assisted", "fixed"
        ]

        resolution_signals = sum(1 for indicator in resolution_indicators if indicator in summary_lower)

        # Check for follow-up necessity indicators
        followup_indicators = [
            "needs follow-up", "requires more", "incomplete", "partially addressed",
            "still unclear", "more questions", "additional help needed"
        ]

        followup_needed = sum(1 for indicator in followup_indicators if indicator in summary_lower)

        # Score resolution effectiveness
        resolution_score = min(10, (resolution_signals * 2) - (followup_needed * 2) + 3)
        resolution_score = max(0, resolution_score)

        # Analyze conversation length efficiency
        total_messages = len(messages)
        efficiency_ratio = 10  # Default high score for short conversations

        if total_messages > 20:
            efficiency_ratio = max(3, 10 - (total_messages - 20) * 0.2)
        elif total_messages > 10:
            efficiency_ratio = max(6, 10 - (total_messages - 10) * 0.3)

        # Identify efficiency patterns
        patterns = []

        if directness_score >= 7:
            patterns.append("direct_responses")
        elif directness_score <= 4:
            patterns.append("indirect_communication")

        if conciseness_score >= 8:
            patterns.append("optimal_response_length")
        elif conciseness_score <= 5:
            patterns.append("length_issues")

        if redundancy_score >= 7:
            patterns.append("minimal_redundancy")
        elif redundancy_score <= 4:
            patterns.append("high_redundancy")

        if resolution_score >= 8:
            patterns.append("effective_resolution")
        elif resolution_score <= 4:
            patterns.append("resolution_challenges")

        if total_messages <= 6:
            patterns.append("efficient_conversation_length")
        elif total_messages > 15:
            patterns.append("extended_conversation")

        # Calculate overall efficiency score
        efficiency_score = (directness_score + conciseness_score +
                          redundancy_score + resolution_score + efficiency_ratio) / 5

        return {
            "status": "success",
            "efficiency_score": round(efficiency_score, 1),
            "directness_score": round(directness_score, 1),
            "conciseness_score": round(conciseness_score, 1),
            "redundancy_score": round(redundancy_score, 1),
            "resolution_score": round(resolution_score, 1),
            "conversation_length_efficiency": round(efficiency_ratio, 1),
            "patterns": patterns,
            "metrics": {
                "total_messages": total_messages,
                "assistant_messages": len(assistant_messages),
                "average_response_length": round(avg_response_length, 1),
                "total_words": total_words,
                "resolution_signals": resolution_signals,
                "followup_needed_indicators": followup_needed,
                "directness_indicators": len(directness_indicators),
                "redundancy_indicators": len(redundancy_indicators)
            }
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Efficiency analysis failed: {str(e)}"}


def analyze_user_satisfaction_indicators(messages: list[dict], summary: str) -> dict:
    """Analyze indicators of user satisfaction and experience quality.

    Identifies satisfaction signals, frustration indicators, and
    overall user experience quality markers.

    Args:
        messages: List of message dictionaries in history_message_schema format.
        summary: Structured summary from the summarizer agent.

    Returns:
        dict: User satisfaction analysis with sentiment and engagement scores.
    """
    try:
        if not isinstance(messages, list):
            return {"status": "error", "error_message": "Messages must be a list"}

        user_messages = [m for m in messages if m.get("role") == "user"]

        if not user_messages:
            return {
                "status": "success",
                "satisfaction_score": 0,
                "sentiment_progression": 0,
                "engagement_score": 0,
                "goal_achievement": 0,
                "patterns": ["no_user_messages"]
            }

        # Analyze positive satisfaction indicators
        positive_phrases = [
            "thank you", "thanks", "helpful", "great", "perfect", "excellent",
            "amazing", "wonderful", "fantastic", "awesome", "appreciate",
            "exactly what i needed", "that works", "solved", "fixed"
        ]

        # Analyze frustration indicators
        frustration_phrases = [
            "frustrated", "confused", "doesn't work", "still don't understand",
            "this is hard", "complicated", "not working", "error", "problem",
            "stuck", "help me", "i'm lost", "unclear", "not sure"
        ]

        # Analyze engagement indicators
        engagement_phrases = [
            "can you also", "what about", "how do i", "could you explain",
            "tell me more", "another question", "follow up", "additionally"
        ]

        # Track sentiment progression through conversation
        sentiment_scores = []
        positive_count = 0
        frustration_count = 0
        engagement_count = 0

        for i, msg in enumerate(user_messages):
            content = str(msg.get("content", "")).lower()

            # Count indicators in this message
            msg_positive = sum(1 for phrase in positive_phrases if phrase in content)
            msg_frustration = sum(1 for phrase in frustration_phrases if phrase in content)
            msg_engagement = sum(1 for phrase in engagement_phrases if phrase in content)

            positive_count += msg_positive
            frustration_count += msg_frustration
            engagement_count += msg_engagement

            # Calculate message sentiment score
            msg_sentiment = (msg_positive * 2) - (msg_frustration * 1.5) + 5  # Base score of 5
            msg_sentiment = max(0, min(10, msg_sentiment))
            sentiment_scores.append(msg_sentiment)

        # Calculate sentiment progression (improvement over time is good)
        if len(sentiment_scores) > 1:
            early_sentiment = sum(sentiment_scores[:len(sentiment_scores)//2]) / max(len(sentiment_scores)//2, 1)
            late_sentiment = sum(sentiment_scores[len(sentiment_scores)//2:]) / max(len(sentiment_scores) - len(sentiment_scores)//2, 1)
            sentiment_progression = late_sentiment - early_sentiment
        else:
            sentiment_progression = 0

        # Normalize progression score
        progression_score = max(0, min(10, sentiment_progression + 5))

        # Calculate overall satisfaction from indicators
        total_messages = len(user_messages)
        satisfaction_ratio = (positive_count - frustration_count) / max(total_messages, 1)
        satisfaction_score = max(0, min(10, (satisfaction_ratio * 5) + 5))

        # Calculate engagement score
        engagement_score = min(10, (engagement_count / max(total_messages, 1)) * 10)

        # Analyze goal achievement from summary and final messages
        summary_lower = str(summary).lower()
        achievement_indicators = [
            "goal achieved", "problem solved", "question answered", "issue resolved",
            "successfully completed", "got what needed", "working now", "understood"
        ]

        goal_signals = sum(1 for indicator in achievement_indicators if indicator in summary_lower)

        # Check final user messages for satisfaction
        if user_messages:
            final_message = str(user_messages[-1].get("content", "")).lower()
            final_satisfaction = sum(1 for phrase in positive_phrases if phrase in final_message)
            final_frustration = sum(1 for phrase in frustration_phrases if phrase in final_message)

            if final_satisfaction > final_frustration:
                goal_signals += 2
            elif final_frustration > 0:
                goal_signals = max(0, goal_signals - 1)

        goal_achievement_score = min(10, goal_signals * 2)

        # Identify satisfaction patterns
        patterns = []

        if satisfaction_score >= 7:
            patterns.append("high_user_satisfaction")
        elif satisfaction_score <= 4:
            patterns.append("user_dissatisfaction_detected")

        if progression_score >= 7:
            patterns.append("improving_user_sentiment")
        elif progression_score <= 3:
            patterns.append("declining_user_sentiment")

        if engagement_score >= 6:
            patterns.append("high_user_engagement")
        elif engagement_score <= 3:
            patterns.append("low_user_engagement")

        if goal_achievement_score >= 8:
            patterns.append("clear_goal_achievement")
        elif goal_achievement_score <= 4:
            patterns.append("unclear_goal_resolution")

        if frustration_count > positive_count and frustration_count > 2:
            patterns.append("significant_user_frustration")

        # Calculate overall user satisfaction score
        overall_score = (satisfaction_score + progression_score +
                        engagement_score + goal_achievement_score) / 4

        return {
            "status": "success",
            "satisfaction_score": round(overall_score, 1),
            "sentiment_progression": round(progression_score, 1),
            "engagement_score": round(engagement_score, 1),
            "goal_achievement": round(goal_achievement_score, 1),
            "raw_satisfaction": round(satisfaction_score, 1),
            "patterns": patterns,
            "metrics": {
                "user_messages_analyzed": len(user_messages),
                "positive_indicators": positive_count,
                "frustration_indicators": frustration_count,
                "engagement_indicators": engagement_count,
                "goal_achievement_signals": goal_signals,
                "sentiment_scores": [round(score, 1) for score in sentiment_scores],
                "avg_sentiment": round(sum(sentiment_scores) / max(len(sentiment_scores), 1), 1)
            }
        }

    except Exception as e:
        return {"status": "error", "error_message": f"User satisfaction analysis failed: {str(e)}"}


def analyze_apple_ecosystem_expertise(messages: list[dict], summary: str) -> dict:
    """Analyze demonstration of Apple ecosystem expertise and knowledge depth.

    Evaluates how well the assistant demonstrates knowledge of Apple platforms,
    hardware, software, and best practices.

    Args:
        messages: List of message dictionaries in history_message_schema format.
        summary: Structured summary from the summarizer agent.

    Returns:
        dict: Apple ecosystem expertise analysis with domain-specific scores.
    """
    try:
        if not isinstance(messages, list):
            return {"status": "error", "error_message": "Messages must be a list"}

        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        if not assistant_messages:
            return {
                "status": "success",
                "ecosystem_expertise_score": 0,
                "platform_knowledge_score": 0,
                "hardware_expertise_score": 0,
                "system_features_score": 0,
                "patterns": ["no_assistant_messages"]
            }

        # First determine if this conversation is about Apple ecosystem topics
        all_content = " ".join([str(msg.get("content", "")).lower() for msg in assistant_messages])
        user_content = " ".join([str(msg.get("content", "")).lower() for msg in [m for m in messages if m.get("role") == "user"]])

        apple_context_phrases = [
            "mac", "macos", "ios", "ipad", "iphone", "apple", "safari", "finder",
            "system preferences", "app store", "xcode", "terminal", "monterey",
            "ventura", "sonoma", "big sur", "silicon", "t2", "secure enclave"
        ]

        apple_context_count = sum(1 for phrase in apple_context_phrases
                                if phrase in all_content or phrase in user_content)

        # If conversation doesn't seem Apple-focused, use appropriate baseline scoring
        if apple_context_count == 0:
            return {
                "status": "success",
                "ecosystem_expertise_score": 6.0,  # Neutral score - no Apple context needed
                "platform_knowledge_score": 6.0,
                "hardware_expertise_score": 6.0,
                "system_features_score": 6.0,
                "ecosystem_thinking_score": 6.0,
                "patterns": ["non_apple_focused_conversation"],
                "metrics": {"apple_context_indicators": 0, "analysis_skipped": True}
            }

        # Analyze platform knowledge (only when Apple context exists)
        platform_terms_found = 0
        hardware_terms_found = 0
        system_features_found = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Check for platform knowledge
            for platform_list in JAMF_KNOWLEDGE["apple_platforms"].values():
                for term in platform_list:
                    if term.lower() in content:
                        if "version" in str(platform_list):
                            platform_terms_found += 1
                        elif "hardware" in str(platform_list) or "M1" in term or "M2" in term or "M3" in term:
                            hardware_terms_found += 1
                        elif "system" in str(platform_list) or "Security" in term:
                            system_features_found += 1

        # Analyze use of Apple-specific terminology and concepts
        apple_concepts = 0
        advanced_concepts = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Basic Apple concepts
            basic_terms = ["macos", "ios", "ipadOS", "safari", "finder", "system preferences", "app store"]
            apple_concepts += sum(1 for term in basic_terms if term in content)

            # Advanced Apple concepts
            advanced_terms = ["system integrity protection", "gatekeeper", "secure boot", "secure enclave",
                            "activation lock", "filevault", "xprotect", "notarization", "sandboxing"]
            advanced_concepts += sum(1 for term in advanced_terms if term in content)

        # Analyze summary for Apple ecosystem context
        summary_lower = str(summary).lower()
        summary_apple_indicators = [
            "apple device", "macos", "ios", "ipad", "macbook", "imac",
            "apple ecosystem", "apple platform", "apple security"
        ]
        summary_signals = sum(1 for indicator in summary_apple_indicators if indicator in summary_lower)

        # Calculate scores with baseline (1-10 scale) - baseline is 5 when Apple context exists
        base_score = 5
        platform_knowledge_score = min(10, base_score + (platform_terms_found * 1.5) + (summary_signals * 0.5))
        hardware_expertise_score = min(10, base_score + (hardware_terms_found * 1.5))
        system_features_score = min(10, base_score + (system_features_found * 1.5) + (advanced_concepts * 0.5))

        # Best practices and ecosystem thinking
        ecosystem_thinking_indicators = [
            "apple ecosystem", "integration", "seamless", "unified", "consistent experience",
            "ecosystem benefits", "apple way", "designed for", "optimized for"
        ]

        ecosystem_thinking = 0
        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()
            ecosystem_thinking += sum(1 for indicator in ecosystem_thinking_indicators if indicator in content)

        ecosystem_thinking_score = min(10, base_score + (ecosystem_thinking * 1.5))

        # Overall ecosystem expertise score
        overall_score = (platform_knowledge_score + hardware_expertise_score +
                        system_features_score + ecosystem_thinking_score) / 4

        # Identify patterns
        patterns = []

        if platform_knowledge_score >= 7:
            patterns.append("strong_platform_knowledge")
        elif platform_knowledge_score <= 3:
            patterns.append("limited_platform_knowledge")

        if hardware_expertise_score >= 6:
            patterns.append("hardware_expertise_demonstrated")
        elif hardware_expertise_score == 0:
            patterns.append("no_hardware_knowledge_shown")

        if system_features_score >= 7:
            patterns.append("advanced_system_knowledge")
        elif system_features_score <= 2:
            patterns.append("basic_system_knowledge")

        if ecosystem_thinking_score >= 6:
            patterns.append("ecosystem_thinking_present")
        elif ecosystem_thinking_score <= 2:
            patterns.append("lacks_ecosystem_perspective")

        if apple_concepts == 0 and advanced_concepts == 0:
            patterns.append("non_apple_focused_conversation")

        return {
            "status": "success",
            "ecosystem_expertise_score": round(overall_score, 1),
            "platform_knowledge_score": round(platform_knowledge_score, 1),
            "hardware_expertise_score": round(hardware_expertise_score, 1),
            "system_features_score": round(system_features_score, 1),
            "ecosystem_thinking_score": round(ecosystem_thinking_score, 1),
            "patterns": patterns,
            "metrics": {
                "platform_terms_found": platform_terms_found,
                "hardware_terms_found": hardware_terms_found,
                "system_features_found": system_features_found,
                "apple_concepts": apple_concepts,
                "advanced_concepts": advanced_concepts,
                "ecosystem_thinking_indicators": ecosystem_thinking,
                "summary_apple_signals": summary_signals
            }
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Apple ecosystem analysis failed: {str(e)}"}


def evaluate_jamf_product_knowledge(messages: list[dict], summary: str) -> dict:
    """Evaluate demonstration of Jamf product knowledge and capabilities.

    Assesses understanding of Jamf Pro, School, Connect, Protect features
    and their appropriate application to user needs.

    Args:
        messages: List of message dictionaries in history_message_schema format.
        summary: Structured summary from the summarizer agent.

    Returns:
        dict: Jamf product knowledge analysis with product-specific scores.
    """
    try:
        if not isinstance(messages, list):
            return {"status": "error", "error_message": "Messages must be a list"}

        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        if not assistant_messages:
            return {
                "status": "success",
                "jamf_knowledge_score": 0,
                "jamf_pro_score": 0,
                "jamf_school_score": 0,
                "jamf_connect_score": 0,
                "jamf_protect_score": 0,
                "patterns": ["no_assistant_messages"]
            }

        # Analyze Jamf product mentions and understanding
        jamf_pro_terms = 0
        jamf_school_terms = 0
        jamf_connect_terms = 0
        jamf_protect_terms = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Count product-specific terminology
            for term in JAMF_KNOWLEDGE["jamf_products"]["jamf_pro"]:
                if term.lower() in content:
                    jamf_pro_terms += 1

            for term in JAMF_KNOWLEDGE["jamf_products"]["jamf_school"]:
                if term.lower() in content:
                    jamf_school_terms += 1

            for term in JAMF_KNOWLEDGE["jamf_products"]["jamf_connect"]:
                if term.lower() in content:
                    jamf_connect_terms += 1

            for term in JAMF_KNOWLEDGE["jamf_products"]["jamf_protect"]:
                if term.lower() in content:
                    jamf_protect_terms += 1

        # Analyze product-appropriate recommendations
        appropriate_recommendations = 0
        product_comparisons = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Look for appropriate product usage recommendations
            recommendation_phrases = [
                "jamf pro for", "use jamf school", "jamf connect helps", "jamf protect provides",
                "recommend jamf", "suggest using", "best suited for", "designed for"
            ]
            appropriate_recommendations += sum(1 for phrase in recommendation_phrases if phrase in content)

            # Look for product comparisons and differentiation
            comparison_phrases = [
                "jamf pro vs", "difference between", "compared to", "instead of",
                "better suited", "more appropriate", "specifically designed"
            ]
            product_comparisons += sum(1 for phrase in comparison_phrases if phrase in content)

        # Analyze feature depth and accuracy
        feature_depth_indicators = 0
        configuration_guidance = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Look for detailed feature explanations
            depth_indicators = [
                "configuration profile", "policy settings", "smart group criteria",
                "prestage enrollment", "self service", "inventory collection",
                "extension attributes", "api integration"
            ]
            feature_depth_indicators += sum(1 for indicator in depth_indicators if indicator in content)

            # Look for configuration guidance
            config_phrases = [
                "configure", "set up", "implement", "deploy", "customize",
                "best practices", "recommended settings", "troubleshoot"
            ]
            configuration_guidance += sum(1 for phrase in config_phrases if phrase in content)

        # Analyze summary for Jamf product context
        summary_lower = str(summary).lower()
        summary_jamf_indicators = [
            "jamf pro", "jamf school", "jamf connect", "jamf protect",
            "jamf solution", "jamf platform", "jamf product"
        ]
        summary_signals = sum(1 for indicator in summary_jamf_indicators if indicator in summary_lower)

        # Calculate product-specific scores (1-10 scale)
        jamf_pro_score = min(10, (jamf_pro_terms * 1.5) + (feature_depth_indicators * 0.5))
        jamf_school_score = min(10, jamf_school_terms * 2)
        jamf_connect_score = min(10, jamf_connect_terms * 2)
        jamf_protect_score = min(10, jamf_protect_terms * 2)

        # Overall product knowledge score
        product_breadth = min(4, sum([
            1 if jamf_pro_terms > 0 else 0,
            1 if jamf_school_terms > 0 else 0,
            1 if jamf_connect_terms > 0 else 0,
            1 if jamf_protect_terms > 0 else 0
        ]))

        overall_score = ((jamf_pro_score + jamf_school_score + jamf_connect_score + jamf_protect_score) / 4 +
                        (appropriate_recommendations * 2) +
                        (product_comparisons * 1.5) +
                        (configuration_guidance * 0.5) +
                        (product_breadth * 1.5) +
                        (summary_signals * 1)) / 6

        overall_score = min(10, overall_score)

        # Identify patterns
        patterns = []

        if jamf_pro_terms >= 3:
            patterns.append("strong_jamf_pro_knowledge")
        elif jamf_pro_terms == 0:
            patterns.append("no_jamf_pro_mention")

        if product_breadth >= 3:
            patterns.append("broad_jamf_product_knowledge")
        elif product_breadth <= 1:
            patterns.append("narrow_jamf_product_focus")

        if appropriate_recommendations >= 2:
            patterns.append("product_appropriate_recommendations")
        elif appropriate_recommendations == 0:
            patterns.append("lacks_product_recommendations")

        if feature_depth_indicators >= 3:
            patterns.append("detailed_feature_knowledge")
        elif feature_depth_indicators == 0:
            patterns.append("surface_level_knowledge")

        if configuration_guidance >= 2:
            patterns.append("practical_implementation_guidance")
        elif configuration_guidance == 0:
            patterns.append("lacks_implementation_details")

        total_jamf_terms = jamf_pro_terms + jamf_school_terms + jamf_connect_terms + jamf_protect_terms
        if total_jamf_terms == 0:
            patterns.append("non_jamf_focused_conversation")

        return {
            "status": "success",
            "jamf_knowledge_score": round(overall_score, 1),
            "jamf_pro_score": round(jamf_pro_score, 1),
            "jamf_school_score": round(jamf_school_score, 1),
            "jamf_connect_score": round(jamf_connect_score, 1),
            "jamf_protect_score": round(jamf_protect_score, 1),
            "product_breadth_score": round(product_breadth * 2.5, 1),
            "patterns": patterns,
            "metrics": {
                "jamf_pro_terms": jamf_pro_terms,
                "jamf_school_terms": jamf_school_terms,
                "jamf_connect_terms": jamf_connect_terms,
                "jamf_protect_terms": jamf_protect_terms,
                "appropriate_recommendations": appropriate_recommendations,
                "product_comparisons": product_comparisons,
                "feature_depth_indicators": feature_depth_indicators,
                "configuration_guidance": configuration_guidance,
                "product_breadth": product_breadth,
                "summary_jamf_signals": summary_signals
            }
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Jamf product knowledge analysis failed: {str(e)}"}


def evaluate_problem_resolution_confidence(messages: list[dict], summary: str) -> dict:
    """Evaluate how confidently problems are resolved and user empowerment.

    Analyzes solution clarity, verification methods, user confidence indicators,
    and empowerment for future self-sufficiency.

    Args:
        messages: List of message dictionaries in history_message_schema format.
        summary: Structured summary from the summarizer agent.

    Returns:
        dict: Problem resolution confidence analysis with empowerment scores.
    """
    try:
        if not isinstance(messages, list):
            return {"status": "error", "error_message": "Messages must be a list"}

        assistant_messages = [m for m in messages if m.get("role") == "assistant"]
        user_messages = [m for m in messages if m.get("role") == "user"]

        if not assistant_messages:
            return {
                "status": "success",
                "resolution_confidence_score": 0,
                "solution_clarity_score": 0,
                "verification_methods_score": 0,
                "user_empowerment_score": 0,
                "patterns": ["no_assistant_messages"]
            }

        # Analyze solution clarity and definitiveness
        solution_clarity_indicators = 0
        definitive_solutions = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Clear solution language
            clear_solution_phrases = [
                "the solution is", "here's how to fix", "to resolve this",
                "the answer is", "you need to", "follow these steps",
                "this will solve", "to fix this issue", "the problem is"
            ]
            solution_clarity_indicators += sum(1 for phrase in clear_solution_phrases if phrase in content)

            # Definitive vs tentative language
            definitive_phrases = [
                "this will work", "guaranteed to", "definitely", "certainly will",
                "this solves", "confirmed solution", "proven method"
            ]
            tentative_phrases = [
                "might work", "could try", "possibly", "may help",
                "worth trying", "sometimes works", "might resolve"
            ]

            definitive_count = sum(1 for phrase in definitive_phrases if phrase in content)
            tentative_count = sum(1 for phrase in tentative_phrases if phrase in content)

            if definitive_count > tentative_count:
                definitive_solutions += 1

        solution_clarity_score = min(10, (solution_clarity_indicators * 2) + (definitive_solutions * 1.5))

        # Analyze verification and testing guidance
        verification_methods = 0
        testing_guidance = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Verification methods
            verification_phrases = [
                "test this", "verify", "check if", "confirm that", "validate",
                "make sure", "ensure that", "double-check", "try this"
            ]
            verification_methods += sum(1 for phrase in verification_phrases if phrase in content)

            # Testing and validation guidance
            testing_phrases = [
                "run a test", "test the configuration", "check the logs",
                "monitor for", "observe the", "look for", "verify in"
            ]
            testing_guidance += sum(1 for phrase in testing_phrases if phrase in content)

        verification_score = min(10, (verification_methods * 1.5) + (testing_guidance * 2))

        # Analyze user empowerment and education
        empowerment_indicators = 0
        educational_content = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Empowerment language
            empowerment_phrases = [
                "now you can", "this allows you to", "you'll be able to",
                "in the future", "next time", "remember to", "keep in mind",
                "understanding this", "now you know", "this way you"
            ]
            empowerment_indicators += sum(1 for phrase in empowerment_phrases if phrase in content)

            # Educational explanations
            educational_phrases = [
                "this works because", "the reason is", "what happens is",
                "behind the scenes", "this ensures", "the purpose of",
                "understanding", "explanation", "how it works"
            ]
            educational_content += sum(1 for phrase in educational_phrases if phrase in content)

        empowerment_score = min(10, (empowerment_indicators * 2) + (educational_content * 1.5))

        # Analyze problem root cause identification
        root_cause_analysis = 0
        preventive_guidance = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Root cause identification
            root_cause_phrases = [
                "the root cause", "this happens because", "the underlying issue",
                "the real problem", "what's actually happening", "the source of"
            ]
            root_cause_analysis += sum(1 for phrase in root_cause_phrases if phrase in content)

            # Preventive measures
            preventive_phrases = [
                "to prevent this", "avoid this by", "in the future",
                "best practice", "recommended approach", "to avoid"
            ]
            preventive_guidance += sum(1 for phrase in preventive_phrases if phrase in content)

        root_cause_score = min(10, (root_cause_analysis * 3) + (preventive_guidance * 2))

        # Analyze summary for resolution indicators
        summary_lower = str(summary).lower()
        resolution_summary_indicators = [
            "problem resolved", "issue fixed", "solution provided", "successfully addressed",
            "user satisfied", "working solution", "effective resolution", "problem solved"
        ]

        confidence_summary_indicators = [
            "clear solution", "definitive answer", "confident resolution",
            "proven method", "reliable fix", "tested solution"
        ]

        summary_resolution_signals = sum(1 for indicator in resolution_summary_indicators if indicator in summary_lower)
        summary_confidence_signals = sum(1 for indicator in confidence_summary_indicators if indicator in summary_lower)

        # Adjust scores based on summary insights
        if summary_resolution_signals > 0:
            solution_clarity_score = min(10, solution_clarity_score + summary_resolution_signals)
        if summary_confidence_signals > 0:
            verification_score = min(10, verification_score + summary_confidence_signals)

        # Identify resolution confidence patterns
        patterns = []

        if solution_clarity_score >= 8:
            patterns.append("high_solution_clarity")
        elif solution_clarity_score <= 4:
            patterns.append("unclear_solutions")

        if verification_score >= 7:
            patterns.append("strong_verification_guidance")
        elif verification_score <= 3:
            patterns.append("lacks_verification_methods")

        if empowerment_score >= 7:
            patterns.append("user_empowerment_focused")
        elif empowerment_score <= 3:
            patterns.append("minimal_user_education")

        if root_cause_score >= 6:
            patterns.append("root_cause_analysis_present")
        elif root_cause_score <= 2:
            patterns.append("surface_level_fixes")

        if definitive_solutions > len(assistant_messages) * 0.7:
            patterns.append("confident_solution_delivery")
        elif definitive_solutions < len(assistant_messages) * 0.3:
            patterns.append("uncertain_solution_approach")

        # Calculate overall resolution confidence score
        resolution_confidence_score = (solution_clarity_score + verification_score +
                                     empowerment_score + root_cause_score) / 4

        return {
            "status": "success",
            "resolution_confidence_score": round(resolution_confidence_score, 1),
            "solution_clarity_score": round(solution_clarity_score, 1),
            "verification_methods_score": round(verification_score, 1),
            "user_empowerment_score": round(empowerment_score, 1),
            "root_cause_analysis_score": round(root_cause_score, 1),
            "patterns": patterns,
            "metrics": {
                "assistant_messages_analyzed": len(assistant_messages),
                "solution_clarity_indicators": solution_clarity_indicators,
                "definitive_solutions": definitive_solutions,
                "verification_methods": verification_methods,
                "testing_guidance": testing_guidance,
                "empowerment_indicators": empowerment_indicators,
                "educational_content": educational_content,
                "root_cause_analysis": root_cause_analysis,
                "preventive_guidance": preventive_guidance,
                "summary_resolution_signals": summary_resolution_signals,
                "summary_confidence_signals": summary_confidence_signals
            }
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Problem resolution confidence analysis failed: {str(e)}"}


def assess_mdm_device_management_concepts(messages: list[dict], summary: str) -> dict:
    """Assess understanding of MDM and device management concepts.

    Evaluates knowledge of enrollment methods, configuration profiles,
    device policies, and mobile device management best practices.

    Args:
        messages: List of message dictionaries in history_message_schema format.
        summary: Structured summary from the summarizer agent.

    Returns:
        dict: MDM device management analysis with domain expertise scores.
    """
    try:
        if not isinstance(messages, list):
            return {"status": "error", "error_message": "Messages must be a list"}

        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        if not assistant_messages:
            return {
                "status": "success",
                "mdm_expertise_score": 0,
                "enrollment_knowledge_score": 0,
                "configuration_profile_score": 0,
                "device_policy_score": 0,
                "patterns": ["no_assistant_messages"]
            }

        # First determine if this conversation is about MDM/device management topics
        all_content = " ".join([str(msg.get("content", "")).lower() for msg in assistant_messages])
        user_content = " ".join([str(msg.get("content", "")).lower() for msg in [m for m in messages if m.get("role") == "user"]])

        mdm_context_phrases = [
            "mdm", "device management", "enrollment", "configuration profile", "policy",
            "mobile device", "device", "profile", "prestage", "dep", "ade", "inventory",
            "self service", "jamf pro", "computer", "supervised", "management"
        ]

        mdm_context_count = sum(1 for phrase in mdm_context_phrases
                              if phrase in all_content or phrase in user_content)

        # If conversation doesn't seem MDM-focused, use appropriate baseline scoring
        if mdm_context_count == 0:
            return {
                "status": "success",
                "mdm_expertise_score": 6.0,  # Neutral score - no MDM context needed
                "enrollment_knowledge_score": 6.0,
                "configuration_profile_score": 6.0,
                "device_policy_score": 6.0,
                "advanced_concepts_score": 6.0,
                "lifecycle_management_score": 6.0,
                "patterns": ["non_mdm_focused_conversation"],
                "metrics": {"mdm_context_indicators": 0, "analysis_skipped": True}
            }

        # Analyze enrollment method knowledge (only when MDM context exists)
        enrollment_terms_found = 0
        enrollment_method_explanations = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Check for enrollment terminology from knowledge base
            for term in JAMF_KNOWLEDGE["mdm_concepts"]["enrollment"]:
                if term.lower() in content:
                    enrollment_terms_found += 1

            # Look for enrollment method explanations
            enrollment_explanation_phrases = [
                "automated device enrollment", "device enrollment program", "manual enrollment",
                "user initiated enrollment", "prestage enrollment", "zero-touch deployment",
                "supervised devices", "unsupervised devices", "enrollment profile"
            ]
            enrollment_method_explanations += sum(1 for phrase in enrollment_explanation_phrases if phrase in content)

        # Apply contextual scoring with baseline of 5 when MDM context exists
        base_score = 5
        enrollment_knowledge_score = min(10, base_score + (enrollment_terms_found * 1) + (enrollment_method_explanations * 1.5))

        # Analyze configuration profile expertise
        config_profile_terms = 0
        profile_implementation_guidance = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Configuration profile concepts
            config_profile_phrases = [
                "configuration profile", "payload", "restriction", "settings payload",
                "profile distribution", "device settings", "user settings", "system configuration"
            ]
            config_profile_terms += sum(1 for phrase in config_profile_phrases if phrase in content)

            # Implementation guidance for profiles
            implementation_phrases = [
                "deploy profile", "install profile", "profile scope", "profile assignment",
                "push profile", "remove profile", "update profile", "profile validation"
            ]
            profile_implementation_guidance += sum(1 for phrase in implementation_phrases if phrase in content)

        config_profile_score = min(10, base_score + (config_profile_terms * 1.5) + (profile_implementation_guidance * 1))

        # Analyze device policy and management understanding
        policy_terms = 0
        management_best_practices = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Policy and management concepts
            policy_phrases = [
                "device policy", "compliance policy", "security policy", "software update policy",
                "app deployment", "inventory collection", "remote commands", "device compliance"
            ]
            policy_terms += sum(1 for phrase in policy_phrases if phrase in content)

            # Management best practices
            best_practice_phrases = [
                "best practice", "recommended approach", "security considerations",
                "deployment strategy", "rollout plan", "testing phase", "pilot group"
            ]
            management_best_practices += sum(1 for phrase in best_practice_phrases if phrase in content)

        policy_score = min(10, base_score + (policy_terms * 1.5) + (management_best_practices * 1))

        # Analyze advanced MDM concepts
        advanced_concepts = 0
        troubleshooting_knowledge = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Advanced MDM concepts
            advanced_mdm_phrases = [
                "scep certificate", "device attestation", "push certificate", "mdm payload",
                "device channel", "user channel", "declarative management", "bootstrap token"
            ]
            advanced_concepts += sum(1 for phrase in advanced_mdm_phrases if phrase in content)

            # Troubleshooting knowledge
            troubleshooting_phrases = [
                "enrollment issues", "profile installation failed", "device not responding",
                "push notification", "certificate renewal", "mdm logs", "device communication"
            ]
            troubleshooting_knowledge += sum(1 for phrase in troubleshooting_phrases if phrase in content)

        advanced_score = min(10, base_score + (advanced_concepts * 1.5) + (troubleshooting_knowledge * 1))

        # Analyze device lifecycle management
        lifecycle_knowledge = 0
        security_focus = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Device lifecycle management
            lifecycle_phrases = [
                "device provisioning", "device retirement", "device refresh", "migration strategy",
                "backup and restore", "device replacement", "end of life", "device handoff"
            ]
            lifecycle_knowledge += sum(1 for phrase in lifecycle_phrases if phrase in content)

            # Security-focused management
            security_phrases = [
                "device encryption", "passcode requirements", "remote wipe", "lost mode",
                "activation lock", "supervised mode", "security restrictions", "compliance monitoring"
            ]
            security_focus += sum(1 for phrase in security_phrases if phrase in content)

        lifecycle_score = min(10, base_score + (lifecycle_knowledge * 1.5) + (security_focus * 1))

        # Analyze summary for MDM context
        summary_lower = str(summary).lower()
        mdm_summary_indicators = [
            "device management", "mobile device", "mdm", "configuration profile",
            "device enrollment", "device policy", "jamf pro management"
        ]
        summary_signals = sum(1 for indicator in mdm_summary_indicators if indicator in summary_lower)

        # Adjust scores based on summary insights
        if summary_signals > 0:
            enrollment_knowledge_score = min(10, enrollment_knowledge_score + summary_signals * 0.5)
            config_profile_score = min(10, config_profile_score + summary_signals * 0.5)

        # Identify MDM expertise patterns
        patterns = []

        if enrollment_knowledge_score >= 7:
            patterns.append("strong_enrollment_expertise")
        elif enrollment_knowledge_score <= 3:
            patterns.append("limited_enrollment_knowledge")

        if config_profile_score >= 7:
            patterns.append("configuration_profile_mastery")
        elif config_profile_score <= 3:
            patterns.append("basic_configuration_knowledge")

        if policy_score >= 6:
            patterns.append("device_policy_expertise")
        elif policy_score <= 2:
            patterns.append("minimal_policy_knowledge")

        if advanced_score >= 6:
            patterns.append("advanced_mdm_concepts")
        elif advanced_score == 0:
            patterns.append("basic_mdm_understanding")

        if lifecycle_score >= 7:
            patterns.append("comprehensive_device_lifecycle")
        elif lifecycle_score <= 3:
            patterns.append("limited_lifecycle_management")

        if security_focus > 3:
            patterns.append("security_focused_approach")

        # Check for integration knowledge
        integration_knowledge = 0
        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()
            integration_phrases = [
                "active directory", "ldap integration", "sso integration", "api integration",
                "third party integration", "directory services", "identity provider"
            ]
            integration_knowledge += sum(1 for phrase in integration_phrases if phrase in content)

        if integration_knowledge >= 2:
            patterns.append("integration_awareness")

        # Calculate overall MDM expertise score
        mdm_expertise_score = (enrollment_knowledge_score + config_profile_score +
                              policy_score + advanced_score + lifecycle_score) / 5

        return {
            "status": "success",
            "mdm_expertise_score": round(mdm_expertise_score, 1),
            "enrollment_knowledge_score": round(enrollment_knowledge_score, 1),
            "configuration_profile_score": round(config_profile_score, 1),
            "device_policy_score": round(policy_score, 1),
            "advanced_concepts_score": round(advanced_score, 1),
            "lifecycle_management_score": round(lifecycle_score, 1),
            "patterns": patterns,
            "metrics": {
                "enrollment_terms_found": enrollment_terms_found,
                "enrollment_method_explanations": enrollment_method_explanations,
                "config_profile_terms": config_profile_terms,
                "profile_implementation_guidance": profile_implementation_guidance,
                "policy_terms": policy_terms,
                "management_best_practices": management_best_practices,
                "advanced_concepts": advanced_concepts,
                "troubleshooting_knowledge": troubleshooting_knowledge,
                "lifecycle_knowledge": lifecycle_knowledge,
                "security_focus": security_focus,
                "integration_knowledge": integration_knowledge,
                "summary_mdm_signals": summary_signals
            }
        }

    except Exception as e:
        return {"status": "error", "error_message": f"MDM device management analysis failed: {str(e)}"}


def analyze_security_compliance_guidance(messages: list[dict], summary: str) -> dict:
    """Analyze security and compliance guidance quality and accuracy.

    Evaluates understanding of security frameworks, compliance requirements,
    Zero Trust principles, and security implementation recommendations.

    Args:
        messages: List of message dictionaries in history_message_schema format.
        summary: Structured summary from the summarizer agent.

    Returns:
        dict: Security compliance analysis with framework knowledge scores.
    """
    try:
        if not isinstance(messages, list):
            return {"status": "error", "error_message": "Messages must be a list"}

        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        if not assistant_messages:
            return {
                "status": "success",
                "security_compliance_score": 0,
                "framework_knowledge_score": 0,
                "zero_trust_score": 0,
                "security_implementation_score": 0,
                "patterns": ["no_assistant_messages"]
            }

        # First determine if this conversation is about security/compliance topics
        security_context_indicators = []
        all_content = " ".join([str(msg.get("content", "")).lower() for msg in assistant_messages])
        user_content = " ".join([str(msg.get("content", "")).lower() for msg in [m for m in messages if m.get("role") == "user"]])

        security_context_phrases = [
            "security", "compliance", "audit", "encrypt", "certificate", "access control",
            "policy", "permission", "authentication", "authorization", "vulnerability",
            "threat", "risk", "privacy", "gdpr", "hipaa", "soc2", "framework"
        ]

        security_context_count = sum(1 for phrase in security_context_phrases
                                   if phrase in all_content or phrase in user_content)

        # If conversation doesn't seem security-focused, use appropriate baseline scoring
        if security_context_count == 0:
            return {
                "status": "success",
                "security_compliance_score": 6.0,  # Neutral score - no security context needed
                "framework_knowledge_score": 6.0,
                "zero_trust_score": 6.0,
                "jamf_security_score": 6.0,
                "security_implementation_score": 6.0,
                "compliance_score": 6.0,
                "privacy_score": 6.0,
                "patterns": ["non_security_focused_conversation"],
                "metrics": {"security_context_indicators": 0, "analysis_skipped": True}
            }

        # Analyze security framework knowledge (only when security context exists)
        framework_terms_found = 0
        framework_explanations = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Check for security framework terminology
            for framework in JAMF_KNOWLEDGE["security_compliance"]["frameworks"]:
                if framework.lower() in content:
                    framework_terms_found += 1

            # Look for framework explanations and applications
            framework_explanation_phrases = [
                "zero trust architecture", "defense in depth", "least privilege access",
                "compliance framework", "security standard", "regulatory requirement",
                "audit requirement", "security assessment", "risk assessment"
            ]
            framework_explanations += sum(1 for phrase in framework_explanation_phrases if phrase in content)

        # Apply contextual scoring - baseline is 5 (neutral) when security topics are present but not deeply discussed
        base_score = 5
        framework_knowledge_score = min(10, base_score + (framework_terms_found * 1.5) + (framework_explanations * 1))

        # Analyze Zero Trust principles understanding
        zero_trust_concepts = 0
        zero_trust_implementation = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Zero Trust concepts
            zero_trust_phrases = [
                "zero trust", "never trust always verify", "verify explicitly",
                "principle of least privilege", "assume breach", "continuous verification",
                "identity verification", "device compliance", "conditional access"
            ]
            zero_trust_concepts += sum(1 for phrase in zero_trust_phrases if phrase in content)

            # Zero Trust implementation guidance
            implementation_phrases = [
                "identity-based security", "device-based access", "network segmentation",
                "micro-segmentation", "continuous monitoring", "risk-based authentication",
                "adaptive access controls", "security posture assessment"
            ]
            zero_trust_implementation += sum(1 for phrase in implementation_phrases if phrase in content)

        zero_trust_score = min(10, base_score + (zero_trust_concepts * 1.5) + (zero_trust_implementation * 1))

        # Analyze Jamf-specific security guidance
        jamf_security_terms = 0
        apple_security_knowledge = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Jamf security features
            for term in JAMF_KNOWLEDGE["security_compliance"]["jamf_security"]:
                if term.lower() in content:
                    jamf_security_terms += 1

            # Apple security features
            for term in JAMF_KNOWLEDGE["security_compliance"]["apple_security"]:
                if term.lower() in content:
                    apple_security_knowledge += 1

        jamf_security_score = min(10, base_score + (jamf_security_terms * 1.5) + (apple_security_knowledge * 1))

        # Analyze security implementation recommendations
        implementation_guidance = 0
        risk_mitigation = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Security implementation guidance
            implementation_phrases = [
                "security best practice", "recommended security", "secure configuration",
                "security policy", "access control", "encryption requirement",
                "certificate management", "secure deployment", "hardening guide"
            ]
            implementation_guidance += sum(1 for phrase in implementation_phrases if phrase in content)

            # Risk mitigation strategies
            risk_phrases = [
                "mitigate risk", "reduce exposure", "security risk", "vulnerability",
                "threat assessment", "risk assessment", "security controls",
                "compensating controls", "defense in depth"
            ]
            risk_mitigation += sum(1 for phrase in risk_phrases if phrase in content)

        implementation_score = min(10, base_score + (implementation_guidance * 1.5) + (risk_mitigation * 1))

        # Analyze compliance-specific guidance
        compliance_knowledge = 0
        audit_preparation = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Compliance terminology and requirements
            compliance_phrases = [
                "compliance requirement", "regulatory compliance", "audit trail",
                "documentation requirement", "policy enforcement", "compliance monitoring",
                "compliance reporting", "evidence collection", "compliance gap"
            ]
            compliance_knowledge += sum(1 for phrase in compliance_phrases if phrase in content)

            # Audit and documentation guidance
            audit_phrases = [
                "audit preparation", "compliance documentation", "evidence gathering",
                "audit report", "compliance assessment", "gap analysis",
                "remediation plan", "compliance dashboard"
            ]
            audit_preparation += sum(1 for phrase in audit_phrases if phrase in content)

        compliance_score = min(10, base_score + (compliance_knowledge * 1.5) + (audit_preparation * 1))

        # Analyze data protection and privacy guidance
        data_protection = 0
        privacy_controls = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Data protection concepts
            data_protection_phrases = [
                "data protection", "data encryption", "data classification",
                "data loss prevention", "data retention", "data governance",
                "personal data", "sensitive data", "data privacy"
            ]
            data_protection += sum(1 for phrase in data_protection_phrases if phrase in content)

            # Privacy controls
            privacy_phrases = [
                "privacy control", "anonymization", "pseudonymization",
                "consent management", "data subject rights", "privacy impact",
                "privacy by design", "privacy policy"
            ]
            privacy_controls += sum(1 for phrase in privacy_phrases if phrase in content)

        privacy_score = min(10, base_score + (data_protection * 1.5) + (privacy_controls * 1.5))

        # Analyze summary for security context
        summary_lower = str(summary).lower()
        security_summary_indicators = [
            "security", "compliance", "zero trust", "framework", "audit",
            "risk", "encryption", "access control", "security policy"
        ]
        summary_signals = sum(1 for indicator in security_summary_indicators if indicator in summary_lower)

        # Adjust scores based on summary insights
        if summary_signals > 0:
            framework_knowledge_score = min(10, framework_knowledge_score + summary_signals * 0.3)
            implementation_score = min(10, implementation_score + summary_signals * 0.3)

        # Identify security compliance patterns
        patterns = []

        if framework_knowledge_score >= 7:
            patterns.append("strong_framework_knowledge")
        elif framework_knowledge_score <= 3:
            patterns.append("limited_framework_understanding")

        if zero_trust_score >= 6:
            patterns.append("zero_trust_expertise")
        elif zero_trust_score <= 2:
            patterns.append("minimal_zero_trust_knowledge")

        if jamf_security_score >= 6:
            patterns.append("jamf_security_expertise")
        elif jamf_security_score == 0:
            patterns.append("no_jamf_security_mention")

        if implementation_score >= 7:
            patterns.append("practical_security_guidance")
        elif implementation_score <= 3:
            patterns.append("theoretical_security_focus")

        if compliance_score >= 6:
            patterns.append("compliance_aware")
        elif compliance_score <= 2:
            patterns.append("compliance_gap")

        if privacy_score >= 5:
            patterns.append("privacy_conscious")

        # Check for holistic security approach
        total_security_knowledge = (framework_terms_found + zero_trust_concepts +
                                  jamf_security_terms + apple_security_knowledge)
        if total_security_knowledge >= 5:
            patterns.append("comprehensive_security_approach")
        elif total_security_knowledge <= 1:
            patterns.append("narrow_security_focus")

        # Calculate overall security compliance score
        security_compliance_score = (framework_knowledge_score + zero_trust_score +
                                   jamf_security_score + implementation_score +
                                   compliance_score + privacy_score) / 6

        return {
            "status": "success",
            "security_compliance_score": round(security_compliance_score, 1),
            "framework_knowledge_score": round(framework_knowledge_score, 1),
            "zero_trust_score": round(zero_trust_score, 1),
            "jamf_security_score": round(jamf_security_score, 1),
            "security_implementation_score": round(implementation_score, 1),
            "compliance_score": round(compliance_score, 1),
            "privacy_score": round(privacy_score, 1),
            "patterns": patterns,
            "metrics": {
                "framework_terms_found": framework_terms_found,
                "framework_explanations": framework_explanations,
                "zero_trust_concepts": zero_trust_concepts,
                "zero_trust_implementation": zero_trust_implementation,
                "jamf_security_terms": jamf_security_terms,
                "apple_security_knowledge": apple_security_knowledge,
                "implementation_guidance": implementation_guidance,
                "risk_mitigation": risk_mitigation,
                "compliance_knowledge": compliance_knowledge,
                "audit_preparation": audit_preparation,
                "data_protection": data_protection,
                "privacy_controls": privacy_controls,
                "summary_security_signals": summary_signals
            }
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Security compliance analysis failed: {str(e)}"}


def assess_implementation_support_quality(messages: list[dict], summary: str) -> dict:
    """Assess quality of implementation support and practical guidance.

    Evaluates step-by-step guidance completeness, risk mitigation strategies,
    change management considerations, and environmental preparation support.

    Args:
        messages: List of message dictionaries in history_message_schema format.
        summary: Structured summary from the summarizer agent.

    Returns:
        dict: Implementation support quality analysis with guidance scores.
    """
    try:
        if not isinstance(messages, list):
            return {"status": "error", "error_message": "Messages must be a list"}

        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        if not assistant_messages:
            return {
                "status": "success",
                "implementation_support_score": 0,
                "step_by_step_guidance_score": 0,
                "risk_mitigation_score": 0,
                "change_management_score": 0,
                "patterns": ["no_assistant_messages"]
            }

        # Analyze step-by-step guidance quality
        step_indicators = 0
        structured_guidance = 0
        sequential_language = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Step-by-step indicators
            step_phrases = [
                "step 1", "step 2", "step 3", "first", "second", "third", "next",
                "then", "after", "before", "finally", "lastly", "step by step"
            ]
            step_indicators += sum(1 for phrase in step_phrases if phrase in content)

            # Structured guidance patterns
            structure_phrases = [
                "here's how", "follow these steps", "process is", "procedure",
                "workflow", "checklist", "instructions", "guide", "walkthrough"
            ]
            structured_guidance += sum(1 for phrase in structure_phrases if phrase in content)

            # Sequential language
            sequential_phrases = [
                "once you", "after you", "when you complete", "upon completion",
                "before proceeding", "ensure that", "verify that", "confirm"
            ]
            sequential_language += sum(1 for phrase in sequential_phrases if phrase in content)

        step_by_step_score = min(10, (step_indicators * 1.5) + (structured_guidance * 2) + (sequential_language * 1))

        # Analyze risk mitigation and preparation guidance
        risk_identification = 0
        mitigation_strategies = 0
        preparation_guidance = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Risk identification
            risk_phrases = [
                "potential risk", "be aware", "caution", "warning", "important note",
                "risk of", "may cause", "could result", "be careful", "consider"
            ]
            risk_identification += sum(1 for phrase in risk_phrases if phrase in content)

            # Mitigation strategies
            mitigation_phrases = [
                "to avoid", "prevent", "mitigate", "reduce risk", "safeguard",
                "backup first", "test environment", "pilot group", "rollback plan"
            ]
            mitigation_strategies += sum(1 for phrase in mitigation_phrases if phrase in content)

            # Preparation guidance
            prep_phrases = [
                "before you start", "preparation", "prerequisites", "requirements",
                "ensure you have", "make sure", "verify access", "check that"
            ]
            preparation_guidance += sum(1 for phrase in prep_phrases if phrase in content)

        risk_mitigation_score = min(10, (risk_identification * 2) + (mitigation_strategies * 2.5) + (preparation_guidance * 1.5))

        # Analyze change management and communication guidance
        stakeholder_communication = 0
        timing_considerations = 0
        impact_assessment = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Stakeholder communication
            communication_phrases = [
                "notify users", "communicate", "inform team", "alert", "announcement",
                "user notification", "end user", "stakeholder", "management approval"
            ]
            stakeholder_communication += sum(1 for phrase in communication_phrases if phrase in content)

            # Timing considerations
            timing_phrases = [
                "maintenance window", "after hours", "business hours", "schedule",
                "timing", "when to deploy", "rollout schedule", "phased approach"
            ]
            timing_considerations += sum(1 for phrase in timing_phrases if phrase in content)

            # Impact assessment
            impact_phrases = [
                "impact on", "affects", "disruption", "downtime", "user experience",
                "business impact", "service interruption", "availability"
            ]
            impact_assessment += sum(1 for phrase in impact_phrases if phrase in content)

        change_management_score = min(10, (stakeholder_communication * 2.5) + (timing_considerations * 2) + (impact_assessment * 2))

        # Analyze environmental and technical considerations
        environment_awareness = 0
        technical_requirements = 0
        compatibility_checks = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Environment awareness
            env_phrases = [
                "production environment", "test environment", "staging", "development",
                "environment specific", "system requirements", "infrastructure"
            ]
            environment_awareness += sum(1 for phrase in env_phrases if phrase in content)

            # Technical requirements
            tech_phrases = [
                "system requirements", "compatibility", "version", "dependencies",
                "prerequisites", "supported", "minimum requirements", "hardware"
            ]
            technical_requirements += sum(1 for phrase in tech_phrases if phrase in content)

            # Compatibility checks
            compat_phrases = [
                "compatible with", "check compatibility", "verify version",
                "supported on", "works with", "compatibility matrix"
            ]
            compatibility_checks += sum(1 for phrase in compat_phrases if phrase in content)

        technical_readiness_score = min(10, (environment_awareness * 2) + (technical_requirements * 1.5) + (compatibility_checks * 2.5))

        # Analyze validation and testing guidance
        testing_guidance = 0
        validation_steps = 0
        troubleshooting_support = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Testing guidance
            testing_phrases = [
                "test this", "validate", "verify", "confirm", "check that",
                "run a test", "pilot test", "proof of concept", "trial run"
            ]
            testing_guidance += sum(1 for phrase in testing_phrases if phrase in content)

            # Validation steps
            validation_phrases = [
                "validation", "verify results", "confirm success", "check logs",
                "monitor", "observe", "expected outcome", "success criteria"
            ]
            validation_steps += sum(1 for phrase in validation_phrases if phrase in content)

            # Troubleshooting support
            troubleshoot_phrases = [
                "if this fails", "troubleshoot", "common issues", "error messages",
                "if you encounter", "problem solving", "diagnostic", "resolve"
            ]
            troubleshooting_support += sum(1 for phrase in troubleshoot_phrases if phrase in content)

        validation_score = min(10, (testing_guidance * 2) + (validation_steps * 1.5) + (troubleshooting_support * 2.5))

        # Analyze documentation and follow-up guidance
        documentation_guidance = 0
        follow_up_support = 0

        for msg in assistant_messages:
            content = str(msg.get("content", "")).lower()

            # Documentation guidance
            doc_phrases = [
                "document", "record", "log", "track changes", "audit trail",
                "evidence", "report", "documentation", "notes"
            ]
            documentation_guidance += sum(1 for phrase in doc_phrases if phrase in content)

            # Follow-up support
            followup_phrases = [
                "follow up", "next steps", "ongoing", "maintenance", "monitoring",
                "regular checks", "periodic review", "continue to"
            ]
            follow_up_support += sum(1 for phrase in followup_phrases if phrase in content)

        documentation_score = min(10, (documentation_guidance * 2.5) + (follow_up_support * 2))

        # Analyze summary for implementation context
        summary_lower = str(summary).lower()
        implementation_summary_indicators = [
            "implementation", "deployment", "rollout", "configuration", "setup",
            "installation", "step by step", "guidance provided", "instructions"
        ]
        summary_signals = sum(1 for indicator in implementation_summary_indicators if indicator in summary_lower)

        # Adjust scores based on summary insights
        if summary_signals > 0:
            step_by_step_score = min(10, step_by_step_score + summary_signals * 0.5)
            risk_mitigation_score = min(10, risk_mitigation_score + summary_signals * 0.3)

        # Identify implementation support patterns
        patterns = []

        if step_by_step_score >= 8:
            patterns.append("excellent_step_by_step_guidance")
        elif step_by_step_score <= 4:
            patterns.append("lacks_structured_guidance")

        if risk_mitigation_score >= 7:
            patterns.append("strong_risk_awareness")
        elif risk_mitigation_score <= 3:
            patterns.append("minimal_risk_consideration")

        if change_management_score >= 6:
            patterns.append("change_management_aware")
        elif change_management_score <= 2:
            patterns.append("lacks_change_management")

        if technical_readiness_score >= 7:
            patterns.append("technical_environment_aware")
        elif technical_readiness_score <= 3:
            patterns.append("limited_environmental_consideration")

        if validation_score >= 7:
            patterns.append("comprehensive_validation_guidance")
        elif validation_score <= 3:
            patterns.append("insufficient_validation_support")

        if documentation_score >= 5:
            patterns.append("documentation_conscious")

        # Check for holistic implementation approach
        total_implementation_signals = (step_indicators + structured_guidance +
                                      risk_identification + mitigation_strategies +
                                      stakeholder_communication + testing_guidance)
        if total_implementation_signals >= 8:
            patterns.append("comprehensive_implementation_support")
        elif total_implementation_signals <= 2:
            patterns.append("basic_implementation_guidance")

        # Calculate overall implementation support score
        implementation_support_score = (step_by_step_score + risk_mitigation_score +
                                      change_management_score + technical_readiness_score +
                                      validation_score + documentation_score) / 6

        return {
            "status": "success",
            "implementation_support_score": round(implementation_support_score, 1),
            "step_by_step_guidance_score": round(step_by_step_score, 1),
            "risk_mitigation_score": round(risk_mitigation_score, 1),
            "change_management_score": round(change_management_score, 1),
            "technical_readiness_score": round(technical_readiness_score, 1),
            "validation_score": round(validation_score, 1),
            "documentation_score": round(documentation_score, 1),
            "patterns": patterns,
            "metrics": {
                "step_indicators": step_indicators,
                "structured_guidance": structured_guidance,
                "sequential_language": sequential_language,
                "risk_identification": risk_identification,
                "mitigation_strategies": mitigation_strategies,
                "preparation_guidance": preparation_guidance,
                "stakeholder_communication": stakeholder_communication,
                "timing_considerations": timing_considerations,
                "impact_assessment": impact_assessment,
                "environment_awareness": environment_awareness,
                "technical_requirements": technical_requirements,
                "compatibility_checks": compatibility_checks,
                "testing_guidance": testing_guidance,
                "validation_steps": validation_steps,
                "troubleshooting_support": troubleshooting_support,
                "documentation_guidance": documentation_guidance,
                "follow_up_support": follow_up_support,
                "summary_implementation_signals": summary_signals
            }
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Implementation support quality analysis failed: {str(e)}"}


def extract_conversation_metadata(messages: list[dict]) -> dict:
    """Extract metadata from a conversation for analysis context.

    Pulls out useful metadata like message counts, timestamps, and
    conversation duration.

    Args:
        messages: List of message dictionaries in history_message_schema format.

    Returns:
        dict: Metadata including message counts, roles, timestamps.
    """
    if not isinstance(messages, list):
        return {"status": "error", "error_message": "Messages must be a list"}

    if not messages:
        return {
            "status": "success",
            "total_messages": 0,
            "user_messages": 0,
            "assistant_messages": 0,
            "has_timestamps": False,
        }

    user_count = sum(1 for m in messages if m.get("role") == "user")
    assistant_count = sum(1 for m in messages if m.get("role") == "assistant")

    # Check for timestamps
    timestamps = [m.get("timestamp") or m.get("created_at") for m in messages]
    has_timestamps = any(timestamps)

    # Calculate average message length
    content_lengths = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            content_lengths.append(len(content))
        elif isinstance(content, list):
            total_len = sum(
                len(item) if isinstance(item, str) else len(item.get("text", ""))
                for item in content
            )
            content_lengths.append(total_len)

    avg_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0

    return {
        "status": "success",
        "total_messages": len(messages),
        "user_messages": user_count,
        "assistant_messages": assistant_count,
        "has_timestamps": has_timestamps,
        "average_message_length": round(avg_length, 1),
        "conversation_turns": min(user_count, assistant_count),
    }


def categorize_feedback(
    category: str,
    severity: str,
    description: str,
    recommendation: str,
) -> dict:
    """Create a structured feedback item for the analysis report.

    Use this to build individual feedback items that will be compiled
    into the final analysis report.

    Args:
        category: Category of feedback (e.g., 'user_experience', 'response_quality',
                  'technical_accuracy', 'communication', 'efficiency').
        severity: Severity level ('low', 'medium', 'high', 'critical').
        description: Description of the observation or issue found.
        recommendation: Suggested improvement or action item.

    Returns:
        dict: Structured feedback item.
    """
    valid_categories = [
        "user_experience",
        "response_quality",
        "technical_accuracy",
        "communication",
        "efficiency",
        "completeness",
        "tone",
        "other",
    ]
    valid_severities = ["low", "medium", "high", "critical"]

    if category.lower() not in valid_categories:
        category = "other"
    if severity.lower() not in valid_severities:
        severity = "medium"

    return {
        "status": "success",
        "feedback_item": {
            "category": category.lower(),
            "severity": severity.lower(),
            "description": description,
            "recommendation": recommendation,
        },
    }


analyzer_agent = Agent(
    name="analyzer_agent",
    model="gemini-2.0-flash",
    description="Agent that performs comprehensive analysis of anonymized conversations using both raw data and summaries.",
    instruction=(
        "You are a conversation analyst that investigates flagged feedback conversations. Your job is to "
        "understand what happened in the conversation and identify potential reasons why an end-user might "
        "have flagged it for review. The flag could be positive (exceptionally good), negative (problematic), "
        "or ambiguous (unclear situation). You have Jamf Software domain expertise to provide context when "
        "conversations involve Apple ecosystem, device management, or Jamf products.\n\n"

        "INPUT FORMAT PARSING:\n"
        "Your input will be formatted as:\n"
        "=== ANONYMIZED MESSAGES ===\n"
        "[Message data here]\n\n"
        "=== SUMMARY ===\n"
        "[Summary data here]\n\n"
        "FIRST: Parse this input to extract the messages and summary separately.\n\n"

        "YOUR INVESTIGATION APPROACH:\n"
        "1. **Parse Input**: Extract messages and summary from the formatted input\n"
        "2. **Basic Analysis**: Use 'extract_conversation_metadata' for conversation structure\n"
        "3. **Core Investigation**: Always run these tools to understand conversation dynamics:\n"
        "   - 'analyze_conversation_flow' - How did the conversation progress?\n"
        "   - 'evaluate_response_quality' - Were responses relevant and helpful?\n"
        "   - 'assess_communication_effectiveness' - Was communication clear and professional?\n"
        "   - 'analyze_technical_accuracy_indicators' - Were responses accurate and confident?\n"
        "   - 'evaluate_efficiency_metrics' - Was the conversation efficient?\n"
        "   - 'analyze_user_satisfaction_indicators' - What signals suggest user sentiment?\n"
        "4. **Domain Context** (when topics are relevant): Use specialized tools for context:\n"
        "   - 'analyze_apple_ecosystem_expertise' - When Apple/macOS/iOS topics discussed\n"
        "   - 'evaluate_jamf_product_knowledge' - When Jamf products mentioned\n"
        "   - 'assess_mdm_device_management_concepts' - When device management is focus\n"
        "   - 'analyze_security_compliance_guidance' - When security topics discussed\n"
        "   - 'evaluate_problem_resolution_confidence' - Always useful for understanding resolution\n"
        "   - 'assess_implementation_support_quality' - Always useful for understanding guidance quality\n"
        "5. **Investigate**: Synthesize findings to understand why this was flagged\n\n"

        "JAMF DOMAIN KNOWLEDGE (Available for Context):\n"
        "- **Apple Platforms**: macOS versions, iOS/iPadOS, Apple Silicon, hardware security features\n"
        "- **Jamf Products**: Jamf Pro (policies, profiles, Self Service), School, Connect, Protect\n"
        "- **MDM Concepts**: Device enrollment, configuration profiles, management policies\n"
        "- **Security**: Zero Trust, compliance frameworks, Apple security features\n\n"

        "WHAT TO INVESTIGATE:\n"
        "**Potential Positive Flagging (User impressed):**\n"
        "- Exceptionally thorough or creative problem-solving\n"
        "- Going above and beyond expectations\n"
        "- Particularly clear explanations or patient guidance\n"
        "- Strong domain expertise when relevant\n"
        "- Efficient resolution of complex issues\n\n"
        "**Potential Negative Flagging (User concerned):**\n"
        "- Communication issues (unclear, unprofessional, impatient)\n"
        "- Incorrect or misleading information\n"
        "- Failure to address the actual problem\n"
        "- Overly complex or confusing guidance\n"
        "- Poor conversation management or closure\n"
        "- Lack of empathy or understanding\n\n"
        "**Ambiguous Situations (Unclear flagging reason):**\n"
        "- Conversations that seem routine but may have subtle issues\n"
        "- Complex technical discussions open to interpretation\n"
        "- Edge cases requiring non-standard approaches\n\n"

        "YOUR INVESTIGATION REPORT:\n"
        "1. **What Happened**: Brief overview of the conversation and main topic\n"
        "2. **Key Findings**: Most significant patterns, issues, or highlights discovered\n"
        "3. **Flagging Investigation**: Why might this have been flagged? (Consider positive, negative, unclear)\n"
        "4. **Conversation Flow**: How well did the interaction progress and conclude?\n"
        "5. **Response Assessment**: Were responses accurate, helpful, and appropriate?\n"
        "6. **Domain Context** (if relevant): Was appropriate Jamf/Apple expertise demonstrated?\n"
        "7. **User Experience**: What likely experience did the end-user have?\n"
        "8. **Confidence**: How confident are you in your analysis?\n\n"

        "INVESTIGATION PRINCIPLES:\n"
        "- **Be Objective**: Look for evidence without assuming positive or negative flagging\n"
        "- **Be Contextual**: Use domain knowledge when relevant, ignore when not applicable\n"
        "- **Be Specific**: Support findings with conversation examples\n"
        "- **Be Balanced**: Consider multiple perspectives and possibilities\n"
        "- **Be Investigative**: Focus on 'what happened?' not 'score against criteria'\n"
        "- **Preserve Anonymity**: Maintain all anonymized placeholders\n\n"

        "Your role is detective, not scorekeeper. Investigate objectively to understand why this "
        "conversation caught the user's attention enough to flag it for review."
    ),
    tools=[
        extract_conversation_metadata,
        categorize_feedback,
        analyze_conversation_flow,
        evaluate_response_quality,
        assess_communication_effectiveness,
        analyze_technical_accuracy_indicators,
        evaluate_efficiency_metrics,
        analyze_user_satisfaction_indicators,
        analyze_apple_ecosystem_expertise,
        evaluate_jamf_product_knowledge,
        assess_mdm_device_management_concepts,
        analyze_security_compliance_guidance,
        evaluate_problem_resolution_confidence,
        assess_implementation_support_quality
    ],
)
