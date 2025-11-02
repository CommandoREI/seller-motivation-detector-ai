"""
Enhanced AI Analysis Module for Seller Motivation Detection
Uses advanced natural language processing and psychological pattern recognition
"""

import re
from datetime import datetime
from typing import Dict, List, Tuple
import os
from openai import OpenAI

class EnhancedMotivationAnalyzer:
    def __init__(self):
        """Initialize the enhanced analyzer with AI capabilities"""
        # Initialize OpenAI client for advanced analysis
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError('OPENAI_API_KEY environment variable not set')
        self.client = OpenAI(api_key=api_key)
        
        # Motivation keywords and phrases (expanded)
        self.high_motivation_keywords = [
            'need to sell quickly', 'behind on payments', 'foreclosure', 'divorce',
            'job loss', 'financial hardship', 'must sell', 'urgent', 'desperate',
            'can\'t afford', 'bankruptcy', 'inherited', 'estate sale', 'relocating',
            'job transfer', 'health issues', 'downsizing', 'retirement', 'medical bills',
            'tax lien', 'pre-foreclosure', 'short sale', 'underwater', 'upside down',
            'can\'t make payments', 'falling apart', 'too much work', 'tired of dealing'
        ]
        
        self.flexibility_indicators = [
            'open to offers', 'negotiable', 'flexible', 'willing to work with',
            'make an offer', 'what can you do', 'cash offer', 'quick close',
            'as-is', 'no repairs', 'seller financing', 'rent back', 'creative terms',
            'whatever works', 'just make it happen', 'work something out'
        ]
        
        self.resistance_indicators = [
            'not in a hurry', 'testing the market', 'see what happens',
            'retail price', 'full asking price', 'no lowball offers',
            'firm on price', 'take my time', 'no rush', 'worth more',
            'comparable sales', 'market value', 'appraised at'
        ]
        
        self.emotional_stress_indicators = [
            'stressed', 'overwhelmed', 'frustrated', 'tired', 'exhausted',
            'can\'t handle', 'too much', 'burden', 'headache', 'nightmare',
            'anxiety', 'worried', 'scared', 'pressure', 'breaking point'
        ]
        
        # Emotional tone patterns
        self.emotion_patterns = {
            'desperation': ['desperate', 'need help', 'please', 'running out of time', 'last resort'],
            'relief': ['relief', 'glad', 'thankful', 'appreciate', 'finally'],
            'frustration': ['frustrated', 'annoyed', 'sick of', 'fed up', 'tired of'],
            'anxiety': ['worried', 'concerned', 'nervous', 'scared', 'anxious'],
            'urgency': ['urgent', 'quickly', 'asap', 'immediately', 'right away', 'soon as possible']
        }

    def analyze_transcript(self, transcript: str) -> Dict:
        """
        Comprehensive analysis of conversation transcript
        Returns detailed motivation analysis with AI-powered insights
        """
        transcript_lower = transcript.lower()
        
        # Basic indicator counting
        high_motivation_score = self._count_indicators(transcript_lower, self.high_motivation_keywords)
        flexibility_score = self._count_indicators(transcript_lower, self.flexibility_indicators)
        resistance_score = self._count_indicators(transcript_lower, self.resistance_indicators)
        emotional_stress_score = self._count_indicators(transcript_lower, self.emotional_stress_indicators)
        
        # Emotion analysis
        emotion_analysis = self._analyze_emotions(transcript_lower)
        
        # Calculate overall motivation (1-10 scale) with enhanced algorithm
        overall_motivation = self._calculate_motivation_score(
            high_motivation_score,
            flexibility_score,
            resistance_score,
            emotional_stress_score,
            emotion_analysis
        )
        
        # Determine motivation level
        motivation_level = self._get_motivation_level(overall_motivation)
        
        # Extract key quotes
        key_quotes = self._extract_key_quotes(transcript, transcript_lower)
        
        # Generate AI-powered insights
        insights = self._generate_ai_insights(transcript, overall_motivation, emotion_analysis)
        
        # Generate negotiation strategy
        strategy = self._generate_negotiation_strategy(
            overall_motivation, 
            flexibility_score, 
            resistance_score,
            emotion_analysis
        )
        
        # Calculate confidence score
        confidence = self._calculate_confidence(
            high_motivation_score,
            flexibility_score,
            len(key_quotes),
            len(transcript.split())
        )
        
        # Extract deal numbers
        deal_numbers = self.extract_deal_numbers(transcript)
        
        return {
            'overall_score': round(overall_motivation, 1),
            'motivation_level': motivation_level,
            'confidence': confidence,
            'key_indicators': {
                'high_motivation': high_motivation_score,
                'flexibility': flexibility_score,
                'resistance': resistance_score,
                'emotional_stress': emotional_stress_score
            },
            'emotion_analysis': emotion_analysis,
            'key_quotes': key_quotes,
            'insights': insights,
            'negotiation_strategy': strategy,
            'timeline_urgency': self._assess_timeline_urgency(transcript_lower),
            'pain_points': self._identify_pain_points(transcript_lower),
            'red_flags': self._identify_red_flags(transcript_lower),
            'conversation_quality': self._assess_conversation_quality(transcript),
            'recommended_offer_approach': self._recommend_offer_approach(overall_motivation, emotion_analysis),
            'deal_numbers': deal_numbers
        }

    def _count_indicators(self, text: str, indicators: List[str]) -> int:
        """Count occurrences of motivation indicators"""
        count = 0
        for indicator in indicators:
            count += text.count(indicator)
        return count

    def _analyze_emotions(self, transcript: str) -> Dict:
        """Analyze emotional tone and patterns in conversation"""
        emotions_detected = {}
        total_emotion_score = 0
        
        for emotion, patterns in self.emotion_patterns.items():
            count = sum(transcript.count(pattern) for pattern in patterns)
            if count > 0:
                emotions_detected[emotion] = count
                total_emotion_score += count
        
        # Determine dominant emotion
        dominant_emotion = max(emotions_detected.items(), key=lambda x: x[1])[0] if emotions_detected else 'neutral'
        
        return {
            'emotions_detected': emotions_detected,
            'dominant_emotion': dominant_emotion,
            'emotional_intensity': min(10, total_emotion_score * 2),
            'emotional_stability': 'unstable' if total_emotion_score > 5 else 'stable'
        }

    def _calculate_motivation_score(
        self, 
        high_motivation: int,
        flexibility: int,
        resistance: int,
        stress: int,
        emotion_analysis: Dict
    ) -> float:
        """Calculate overall motivation score using enhanced algorithm"""
        base_score = 5.0
        
        # Motivation boosters
        motivation_boost = min(high_motivation * 0.8, 3.5)
        flexibility_boost = min(flexibility * 0.6, 2.0)
        stress_boost = min(stress * 0.4, 1.5)
        
        # Emotional intensity boost
        emotion_boost = min(emotion_analysis['emotional_intensity'] * 0.15, 1.0)
        
        # Resistance penalty
        resistance_penalty = min(resistance * 0.7, 3.0)
        
        # Calculate final score
        final_score = base_score + motivation_boost + flexibility_boost + stress_boost + emotion_boost - resistance_penalty
        
        # Clamp between 1 and 10
        return max(1.0, min(10.0, final_score))

    def _get_motivation_level(self, score: float) -> str:
        """Convert numeric score to motivation level"""
        if score >= 8.5:
            return "Extremely High"
        elif score >= 7.0:
            return "Very High"
        elif score >= 5.5:
            return "High"
        elif score >= 4.0:
            return "Moderate"
        elif score >= 2.5:
            return "Low"
        else:
            return "Very Low"

    def _extract_key_quotes(self, original_transcript: str, lower_transcript: str) -> List[str]:
        """Extract important quotes from the conversation"""
        quotes = []
        lines = original_transcript.split('\n')
        
        # Look for seller lines (lines that start with "Seller:" or similar)
        seller_pattern = re.compile(r'(seller|owner|homeowner):', re.IGNORECASE)
        
        for line in lines:
            line_lower = line.lower()
            
            # Prioritize seller quotes
            if seller_pattern.search(line):
                # Look for lines with high motivation indicators
                for keyword in self.high_motivation_keywords[:15]:
                    if keyword in line_lower and len(line.strip()) > 20:
                        # Clean the quote
                        cleaned = re.sub(r'^(seller|owner|homeowner):\s*', '', line.strip(), flags=re.IGNORECASE)
                        if cleaned and len(cleaned) > 20:
                            quotes.append(cleaned)
                        break
        
        # If we don't have enough quotes, look for any impactful lines
        if len(quotes) < 3:
            for line in lines:
                line_lower = line.lower()
                for keyword in self.high_motivation_keywords + self.emotional_stress_indicators:
                    if keyword in line_lower and len(line.strip()) > 20 and line.strip() not in quotes:
                        cleaned = re.sub(r'^(seller|owner|homeowner|agent|investor):\s*', '', line.strip(), flags=re.IGNORECASE)
                        if cleaned and len(cleaned) > 20:
                            quotes.append(cleaned)
                        break
                if len(quotes) >= 5:
                    break
        
        return quotes[:5]  # Return top 5 quotes

    def _generate_ai_insights(self, transcript: str, motivation_score: float, emotion_analysis: Dict) -> List[str]:
        """Generate AI-powered insights using LLM"""
        insights = []
        transcript_lower = transcript.lower()
        
        # Rule-based insights (fast and reliable)
        if 'behind on payments' in transcript_lower or 'foreclosure' in transcript_lower:
            insights.append("🚨 Financial distress detected - seller facing foreclosure pressure, highly motivated")
        
        if 'divorce' in transcript_lower:
            insights.append("💔 Divorce situation - emotional urgency to liquidate and split assets quickly")
        
        if 'job' in transcript_lower and ('loss' in transcript_lower or 'transfer' in transcript_lower or 'relocation' in transcript_lower):
            insights.append("💼 Employment change - timeline driven by job situation, likely inflexible deadline")
        
        if 'inherited' in transcript_lower or 'estate' in transcript_lower:
            insights.append("🏠 Inherited property - low emotional attachment, motivated by cash liquidation")
        
        if 'health' in transcript_lower or 'medical' in transcript_lower:
            insights.append("🏥 Health-related sale - potential urgency and financial pressure from medical costs")
        
        # Emotional insights
        if emotion_analysis['dominant_emotion'] == 'desperation':
            insights.append("😰 High desperation detected - seller in crisis mode, maximum negotiation leverage")
        elif emotion_analysis['dominant_emotion'] == 'urgency':
            insights.append("⏰ Strong time pressure - emphasize speed and certainty in your offer")
        elif emotion_analysis['dominant_emotion'] == 'frustration':
            insights.append("😤 Seller frustrated with property - position as problem solver, not just buyer")
        
        # Motivation-based insights
        if motivation_score >= 8.0:
            insights.append("✅ Extremely high motivation - seller likely to accept reasonable offers below market")
        elif motivation_score >= 6.5:
            insights.append("📊 Strong motivation detected - good opportunity for favorable terms")
        elif motivation_score <= 3.5:
            insights.append("⚠️ Low motivation - seller may be testing market, qualify carefully before investing time")
        
        # Add AI-generated insight using LLM (if transcript is substantial)
        if len(transcript.split()) > 50:
            try:
                ai_insight = self._get_llm_insight(transcript, motivation_score)
                if ai_insight:
                    insights.append(f"🤖 AI Analysis: {ai_insight}")
            except:
                pass  # Fail gracefully if AI analysis unavailable
        
        return insights if insights else ["Standard motivation level - typical seller situation"]

    def _get_llm_insight(self, transcript: str, motivation_score: float) -> str:
        """Get AI-generated insight using LLM"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert real estate negotiation analyst. Analyze seller conversations and provide ONE key strategic insight in 15 words or less."
                    },
                    {
                        "role": "user",
                        "content": f"Motivation Score: {motivation_score}/10\n\nConversation:\n{transcript[:1000]}\n\nProvide ONE strategic insight for the investor:"
                    }
                ],
                max_tokens=50,
                temperature=0.7
            )
            
            insight = response.choices[0].message.content.strip()
            return insight if len(insight) < 150 else insight[:147] + "..."
        except:
            return ""

    def _generate_negotiation_strategy(
        self, 
        motivation_score: float, 
        flexibility_score: int, 
        resistance_score: int,
        emotion_analysis: Dict
    ) -> List[str]:
        """Generate comprehensive negotiation strategy recommendations"""
        strategies = []
        
        # High motivation strategies
        if motivation_score >= 8.0:
            strategies.append("🎯 Lead with SPEED and CERTAINTY - emphasize quick closing (7-14 days)")
            strategies.append("💡 Position as PROBLEM SOLVER, not just buyer - focus on their pain relief")
            strategies.append("💰 Offer 60-70% ARV - they're motivated enough to accept below-market pricing")
        elif motivation_score >= 6.5:
            strategies.append("⚡ Emphasize quick closing timeline (14-30 days)")
            strategies.append("🤝 Build rapport and trust - they need confidence you'll close")
            strategies.append("💵 Offer 65-75% ARV - good opportunity for favorable terms")
        
        # Flexibility strategies
        if flexibility_score >= 2:
            strategies.append("🔄 Explore CREATIVE TERMS - seller financing, lease options, rent-back")
            strategies.append("📋 Present multiple offer structures - let them choose what works best")
        
        # Resistance handling
        if resistance_score >= 2:
            strategies.append("📊 Build VALUE PROPOSITION carefully - use comps and market data")
            strategies.append("⏳ Multiple touchpoints needed - don't expect immediate acceptance")
            strategies.append("🎓 Educate on market realities - help them understand true market value")
        
        # Emotional approach
        dominant_emotion = emotion_analysis.get('dominant_emotion', 'neutral')
        if dominant_emotion == 'desperation':
            strategies.append("❤️ Show empathy and understanding - they need emotional support")
            strategies.append("🛡️ Be the 'safe choice' - reduce their fear and uncertainty")
        elif dominant_emotion == 'frustration':
            strategies.append("🔧 Position as SOLUTION to their frustration - take the burden away")
        elif dominant_emotion == 'urgency':
            strategies.append("⏱️ Match their urgency - show you can move at their speed")
        
        # Low motivation strategies
        if motivation_score <= 4.0:
            strategies.append("🔍 QUALIFY CAREFULLY - may not be serious, don't waste time")
            strategies.append("📚 Focus on education and relationship building for future opportunity")
            strategies.append("📞 Stay in touch - motivation may increase over time")
        
        # Default strategy
        if not strategies:
            strategies.append("📄 Standard approach - present fair offer with clear terms")
            strategies.append("🤝 Build relationship and trust through professional presentation")
        
        return strategies

    def _assess_timeline_urgency(self, transcript: str) -> str:
        """Assess timeline urgency from conversation"""
        urgent_keywords = ['urgent', 'quickly', 'asap', 'soon', 'days', 'week', 'immediately', 'right away']
        moderate_keywords = ['month', 'months', 'few weeks', 'spring', 'summer', 'fall', 'winter']
        
        urgent_count = sum(transcript.count(keyword) for keyword in urgent_keywords)
        moderate_count = sum(transcript.count(keyword) for keyword in moderate_keywords)
        
        if urgent_count >= 2:
            return "🔴 CRITICAL - Seller needs to close within days/weeks"
        elif urgent_count >= 1:
            return "🟠 HIGH - Seller indicated time pressure (weeks to 1 month)"
        elif moderate_count >= 1:
            return "🟡 MODERATE - Seller has preferred timeline (1-3 months)"
        else:
            return "🟢 LOW - No specific timeline mentioned, flexible"

    def _identify_pain_points(self, transcript: str) -> List[str]:
        """Identify seller's main pain points"""
        pain_points = []
        
        pain_point_map = {
            'Financial Pressure': ['payments', 'mortgage', 'behind', 'afford', 'foreclosure', 'bankruptcy'],
            'Property Condition': ['maintenance', 'repairs', 'falling apart', 'needs work', 'condition'],
            'Geographic Distance': ['distance', 'far', 'out of state', 'moved', 'relocated'],
            'Tenant Issues': ['tenants', 'rental', 'eviction', 'bad tenants', 'vacancy'],
            'Time Burden': ['time', 'busy', 'can\'t manage', 'too much work', 'overwhelming'],
            'Emotional Stress': ['divorce', 'death', 'estate', 'health', 'family'],
            'Market Concerns': ['market', 'value dropping', 'won\'t sell', 'sitting too long']
        }
        
        for pain_point, keywords in pain_point_map.items():
            if any(keyword in transcript for keyword in keywords):
                pain_points.append(pain_point)
        
        return pain_points if pain_points else ["Standard selling motivations"]

    def _identify_red_flags(self, transcript: str) -> List[str]:
        """Identify potential red flags or concerns"""
        red_flags = []
        
        if 'attorney' in transcript or 'lawyer' in transcript:
            red_flags.append("⚖️ Legal representation involved - may complicate negotiations")
        
        if 'other offers' in transcript or 'multiple offers' in transcript or 'another buyer' in transcript:
            red_flags.append("🏃 Competition from other buyers - may need to move quickly")
        
        if 'think about it' in transcript or 'get back to you' in transcript or 'let me know' in transcript:
            red_flags.append("🤔 Seller needs time to decide - may not be ready to commit")
        
        if 'spouse' in transcript and 'talk to' in transcript:
            red_flags.append("👥 Decision maker not present - additional approval needed")
        
        if 'realtor' in transcript or 'agent' in transcript or 'listed' in transcript:
            red_flags.append("🏢 Real estate agent involved - may have commission expectations")
        
        if 'appraisal' in transcript or 'appraised' in transcript:
            red_flags.append("📋 Seller anchored to appraisal value - education needed on investor pricing")
        
        if 'not in a hurry' in transcript or 'no rush' in transcript:
            red_flags.append("⏰ No urgency - seller may be testing market, qualify carefully")
        
        return red_flags

    def _assess_conversation_quality(self, transcript: str) -> Dict:
        """Assess the quality and depth of conversation"""
        word_count = len(transcript.split())
        line_count = len([line for line in transcript.split('\n') if line.strip()])
        
        # Determine quality
        if word_count > 200 and line_count > 10:
            quality = "Excellent"
            detail_level = "High"
        elif word_count > 100 and line_count > 5:
            quality = "Good"
            detail_level = "Moderate"
        else:
            quality = "Limited"
            detail_level = "Low"
        
        return {
            'quality': quality,
            'word_count': word_count,
            'exchange_count': line_count,
            'detail_level': detail_level
        }

    def _recommend_offer_approach(self, motivation_score: float, emotion_analysis: Dict) -> Dict:
        """Recommend specific offer approach based on analysis"""
        if motivation_score >= 8.0:
            return {
                'offer_range': '60-70% ARV',
                'closing_timeline': '7-14 days',
                'terms': 'All cash, as-is, no contingencies',
                'presentation_style': 'Confident and solution-focused',
                'follow_up': 'Immediate - strike while motivation is high'
            }
        elif motivation_score >= 6.5:
            return {
                'offer_range': '65-75% ARV',
                'closing_timeline': '14-30 days',
                'terms': 'Cash preferred, minimal contingencies',
                'presentation_style': 'Professional with empathy',
                'follow_up': 'Within 24-48 hours'
            }
        elif motivation_score >= 4.5:
            return {
                'offer_range': '70-80% ARV',
                'closing_timeline': '30-45 days',
                'terms': 'Standard investor terms',
                'presentation_style': 'Educational and relationship-building',
                'follow_up': 'Within 3-5 days, stay in touch'
            }
        else:
            return {
                'offer_range': '75-85% ARV (if pursuing)',
                'closing_timeline': 'Flexible',
                'terms': 'Standard terms',
                'presentation_style': 'Exploratory and educational',
                'follow_up': 'Low priority - focus on better leads'
            }

    def _calculate_confidence(self, motivation_count: int, flexibility_count: int, quote_count: int, word_count: int) -> int:
        """Calculate confidence score for the analysis"""
        base_confidence = 70
        
        # More indicators = higher confidence
        indicator_boost = min((motivation_count + flexibility_count) * 3, 15)
        
        # More quotes = higher confidence
        quote_boost = min(quote_count * 2, 10)
        
        # Longer conversation = higher confidence
        length_boost = min(word_count // 50, 10)
        
        total_confidence = base_confidence + indicator_boost + quote_boost + length_boost
        
        return min(98, max(65, total_confidence))

    def extract_deal_numbers(self, transcript: str) -> Dict:
        """
        Extract financial numbers and property details from conversation using AI
        Returns structured data about the deal
        """
        try:
            # Use GPT to extract deal numbers with structured output
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": """You are an expert at extracting financial and property information from real estate conversations.
Extract all relevant numbers and details mentioned in the conversation.
Return ONLY valid JSON with the exact structure requested.
Use null for missing values. Do not make up numbers."""},
                    {"role": "user", "content": f"""Extract deal numbers from this conversation:

{transcript}

Return JSON with these fields (use null if not mentioned):
{{
  "mortgage_balance": number or null,
  "arrears": number or null,
  "months_behind": number or null,
  "monthly_payment": number or null,
  "seller_net_desired": number or null,
  "asking_price": number or null,
  "estimated_value": number or null,
  "property_taxes_annual": number or null,
  "hoa_monthly": number or null,
  "repair_costs": number or null,
  "bedrooms": number or null,
  "bathrooms": number or null,
  "square_feet": number or null,
  "interest_rate": number or null,
  "days_until_foreclosure": number or null,
  "additional_notes": "string with any other relevant context"
}}"""}
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            import json
            extracted_data = json.loads(response.choices[0].message.content)
            
            # Calculate derived values
            mortgage_balance = extracted_data.get('mortgage_balance') or 0
            arrears = extracted_data.get('arrears') or 0
            seller_net = extracted_data.get('seller_net_desired') or 0
            estimated_value = extracted_data.get('estimated_value') or 0
            
            total_payoff = mortgage_balance + arrears if mortgage_balance > 0 else None
            minimum_offer = total_payoff + seller_net if total_payoff and seller_net else None
            equity_available = estimated_value - total_payoff if estimated_value > 0 and total_payoff else None
            
            # Count how many fields were extracted
            fields_extracted = sum(1 for v in extracted_data.values() if v is not None and v != "" and v != 0)
            
            # Calculate confidence based on fields extracted
            confidence = min(95, max(30, fields_extracted * 8))
            
            return {
                'extracted': extracted_data,
                'calculated': {
                    'total_payoff': total_payoff,
                    'minimum_offer': minimum_offer,
                    'equity_available': equity_available
                },
                'confidence': confidence,
                'fields_extracted': fields_extracted
            }
            
        except Exception as e:
            print(f"Error extracting deal numbers: {str(e)}")
            return {
                'extracted': {},
                'calculated': {},
                'confidence': 0,
                'fields_extracted': 0,
                'error': str(e)
            }
