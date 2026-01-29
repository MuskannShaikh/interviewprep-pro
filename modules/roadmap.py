"""
AI Insights Module
Provides AI-powered analysis and recommendations
"""

import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager
from typing import List, Dict

class AIInsights:
    """Generates AI-powered insights from interview data"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.use_real_ai = False  # Toggle for real AI API
    
    def show_insights_page(self, user_id: int):
        """Display AI insights page"""
        
        st.title("🤖 AI-Powered Insights")
        st.markdown("Get intelligent recommendations based on your interview performance")
        
        # Get interview data
        interviews = self.db.get_user_interviews(user_id)
        
        if not interviews:
            st.info("📋 No data available for analysis. Add some interviews first!")
            return
        
        df = pd.DataFrame(interviews)
        
        # Display different insight sections
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Performance Analysis",
            "🎯 Weak Area Detection",
            "💡 Personalized Tips",
            "🔮 Predictions"
        ])
        
        with tab1:
            self._show_performance_analysis(df)
        
        with tab2:
            self._show_weak_area_detection(df, user_id)
        
        with tab3:
            self._show_personalized_tips(df)
        
        with tab4:
            self._show_predictions(df)
    
    def _show_performance_analysis(self, df: pd.DataFrame):
        """Analyze overall performance"""
        
        st.subheader("📊 Your Performance Summary")
        
        total = len(df)
        selected = len(df[df['status'] == 'Selected'])
        rejected = len(df[df['status'] == 'Rejected'])
        interviewed = len(df[df['status'] == 'Interviewed'])
        
        success_rate = (selected / total * 100) if total > 0 else 0
        interview_conversion = (interviewed / total * 100) if total > 0 else 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Overall Success Rate", f"{success_rate:.1f}%")
            st.metric("Interview Conversion Rate", f"{interview_conversion:.1f}%")
        
        with col2:
            avg_prep = df['preparation_level'].mean()
            st.metric("Average Preparation Level", f"{avg_prep:.2f}/5.0")
            
            if selected > 0:
                selected_prep = df[df['status'] == 'Selected']['preparation_level'].mean()
                st.metric("Avg Prep (Selected)", f"{selected_prep:.2f}/5.0")
        
        # AI Analysis
        st.markdown("---")
        st.subheader("🤖 AI Analysis")
        
        analysis = self._generate_performance_analysis(df)
        st.info(analysis)
        
        # Comparison with benchmarks
        st.markdown("---")
        st.subheader("📈 Industry Benchmarks")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Your Success Rate",
                f"{success_rate:.1f}%",
                delta=f"{success_rate - 15:.1f}% vs avg" if success_rate > 15 else f"{success_rate - 15:.1f}% vs avg",
                delta_color="normal"
            )
        
        with col2:
            st.metric(
                "Industry Average",
                "15%",
                help="Typical success rate in tech interviews"
            )
        
        with col3:
            performance = "Excellent" if success_rate > 20 else "Good" if success_rate > 10 else "Needs Improvement"
            st.metric("Performance Rating", performance)
    
    def _show_weak_area_detection(self, df: pd.DataFrame, user_id: int):
        """Detect and display weak areas"""
        
        st.subheader("🎯 Weak Area Detection")
        
        # Analyze by technical topics
        if 'technical_topics' in df.columns:
            topics_data = []
            
            for idx, row in df.iterrows():
                if row['technical_topics']:
                    topics = [t.strip() for t in row['technical_topics'].split(',')]
                    for topic in topics:
                        topics_data.append({
                            'topic': topic,
                            'status': row['status'],
                            'prep_level': row['preparation_level']
                        })
            
            if topics_data:
                topics_df = pd.DataFrame(topics_data)
                
                # Calculate success rate per topic
                topic_analysis = []
                for topic in topics_df['topic'].unique():
                    topic_rows = topics_df[topics_df['topic'] == topic]
                    total = len(topic_rows)
                    selected = len(topic_rows[topic_rows['status'] == 'Selected'])
                    success_rate = (selected / total * 100) if total > 0 else 0
                    avg_prep = topic_rows['prep_level'].mean()
                    
                    topic_analysis.append({
                        'Topic': topic,
                        'Success Rate (%)': success_rate,
                        'Avg Preparation': avg_prep,
                        'Attempts': total
                    })
                
                topic_df = pd.DataFrame(topic_analysis).sort_values('Success Rate (%)')
                
                st.dataframe(topic_df, use_container_width=True)
                
                # Identify weak areas
                weak_topics = topic_df[topic_df['Success Rate (%)'] < 20].head(3)
                
                if not weak_topics.empty:
                    st.warning("⚠️ **Areas Needing Improvement:**")
                    for idx, topic in weak_topics.iterrows():
                        st.write(f"- **{topic['Topic']}**: {topic['Success Rate (%)']:.1f}% success rate ({topic['Attempts']} attempts)")
                    
                    # AI recommendations
                    st.markdown("---")
                    st.subheader("💡 AI Recommendations")
                    recommendations = self._generate_weak_area_recommendations(weak_topics)
                    st.success(recommendations)
            else:
                st.info("Add technical topics to your interviews to get detailed analysis!")
        
        # Analyze by preparation level
        st.markdown("---")
        st.subheader("📊 Preparation vs Outcome Analysis")
        
        prep_analysis = []
        for prep in range(1, 6):
            prep_df = df[df['preparation_level'] == prep]
            if len(prep_df) > 0:
                selected = len(prep_df[prep_df['status'] == 'Selected'])
                rejected = len(prep_df[prep_df['status'] == 'Rejected'])
                prep_analysis.append({
                    'Preparation Level': prep,
                    'Total': len(prep_df),
                    'Selected': selected,
                    'Rejected': rejected,
                    'Success Rate (%)': (selected / len(prep_df) * 100)
                })
        
        if prep_analysis:
            prep_df = pd.DataFrame(prep_analysis)
            st.dataframe(prep_df, use_container_width=True)
            
            # Key insight
            best_prep = prep_df.loc[prep_df['Success Rate (%)'].idxmax()]
            st.success(f"🎯 Your sweet spot is preparation level {int(best_prep['Preparation Level'])} with {best_prep['Success Rate (%)']:.1f}% success rate!")
    
    def _show_personalized_tips(self, df: pd.DataFrame):
        """Show personalized improvement tips"""
        
        st.subheader("💡 Personalized Improvement Tips")
        
        tips = self._generate_personalized_tips(df)
        
        for i, tip in enumerate(tips, 1):
            with st.expander(f"📌 Tip {i}: {tip['title']}", expanded=(i == 1)):
                st.write(tip['description'])
                st.info(f"💡 **Action:** {tip['action']}")
    
    def _show_predictions(self, df: pd.DataFrame):
        """Show AI predictions"""
        
        st.subheader("🔮 AI Predictions & Trends")
        
        # Predict next interview success probability
        recent_df = df.tail(5)
        avg_recent_prep = recent_df['preparation_level'].mean()
        recent_success_rate = (len(recent_df[recent_df['status'] == 'Selected']) / len(recent_df) * 100) if len(recent_df) > 0 else 0
        
        st.markdown("### 🎯 Next Interview Success Probability")
        
        # Simple prediction model
        success_prob = min(95, (avg_recent_prep * 15 + recent_success_rate * 0.5))
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Predicted Success Rate", f"{success_prob:.1f}%")
        
        with col2:
            st.metric("Based on Last 5 Interviews", f"{recent_success_rate:.1f}%")
        
        with col3:
            st.metric("Your Avg Preparation", f"{avg_recent_prep:.1f}/5.0")
        
        # Trend analysis
        st.markdown("---")
        st.markdown("### 📈 Performance Trend")
        
        if len(df) >= 5:
            early_success = len(df.head(len(df)//2)[df.head(len(df)//2)['status'] == 'Selected']) / (len(df)//2) * 100
            late_success = len(df.tail(len(df)//2)[df.tail(len(df)//2)['status'] == 'Selected']) / (len(df)//2) * 100
            
            trend = "improving" if late_success > early_success else "declining" if late_success < early_success else "stable"
            trend_emoji = "📈" if trend == "improving" else "📉" if trend == "declining" else "➡️"
            
            st.info(f"{trend_emoji} Your performance is **{trend}**: Early success rate: {early_success:.1f}% → Recent success rate: {late_success:.1f}%")
        else:
            st.info("Add more interviews to see performance trends!")
    
    def _generate_performance_analysis(self, df: pd.DataFrame) -> str:
        """Generate AI performance analysis"""
        
        total = len(df)
        selected = len(df[df['status'] == 'Selected'])
        success_rate = (selected / total * 100) if total > 0 else 0
        avg_prep = df['preparation_level'].mean()
        
        analysis = f"""
**AI Performance Analysis:**

Based on your {total} interview(s):

- You have a **{success_rate:.1f}% success rate**, which is {'above' if success_rate > 15 else 'at' if success_rate == 15 else 'below'} the industry average of 15%.

- Your average preparation level is **{avg_prep:.2f}/5.0**, suggesting you {'generally prepare well' if avg_prep >= 3.5 else 'could improve your preparation'}.

- {'You are doing great! Keep maintaining your preparation standards.' if success_rate > 20 else 'Focus on increasing your preparation time and practice to improve success rates.' if success_rate < 10 else 'Good progress! Consider targeting higher preparation levels for better results.'}
        """
        
        return analysis.strip()
    
    def _generate_weak_area_recommendations(self, weak_topics: pd.DataFrame) -> str:
        """Generate recommendations for weak areas"""
        
        recommendations = "**Recommended Action Plan:**\n\n"
        
        for idx, topic in weak_topics.iterrows():
            recommendations += f"• **{topic['Topic']}**: "
            
            if topic['Avg Preparation'] < 3:
                recommendations += f"Increase preparation (current: {topic['Avg Preparation']:.1f}/5). Dedicate 2-3 hours daily for this topic.\n"
            else:
                recommendations += f"Your preparation is good, but success rate is low. Consider getting mock interviews focused on {topic['Topic']}.\n"
        
        recommendations += "\n**General Tips:**\n"
        recommendations += "• Practice problems daily on platforms like LeetCode, HackerRank\n"
        recommendations += "• Join study groups or find an accountability partner\n"
        recommendations += "• Review failed interview topics and create a study schedule\n"
        
        return recommendations
    
    def _generate_personalized_tips(self, df: pd.DataFrame) -> List[Dict]:
        """Generate personalized improvement tips"""
        
        tips = []
        
        # Tip based on preparation level
        avg_prep = df['preparation_level'].mean()
        if avg_prep < 3:
            tips.append({
                'title': 'Increase Your Preparation Time',
                'description': f'Your average preparation level is {avg_prep:.2f}/5. Studies show that preparation levels above 3.5 significantly increase success rates.',
                'action': 'Set aside 2-3 hours daily for focused interview preparation. Create a structured study plan.'
            })
        
        # Tip based on success rate
        success_rate = len(df[df['status'] == 'Selected']) / len(df) * 100 if len(df) > 0 else 0
        if success_rate < 15:
            tips.append({
                'title': 'Master the Fundamentals',
                'description': 'Your current success rate suggests focusing on core concepts would be beneficial.',
                'action': 'Spend the next 2 weeks on fundamentals: Data Structures, Algorithms, and System Design basics.'
            })
        
        # Tip based on interview frequency
        if len(df) < 5:
            tips.append({
                'title': 'Apply to More Companies',
                'description': 'Increasing your application volume improves both experience and opportunities.',
                'action': 'Set a goal to apply to 10-15 companies per week. Track each application in this system.'
            })
        
        # Generic tips
        tips.extend([
            {
                'title': 'Practice Mock Interviews',
                'description': 'Mock interviews are proven to reduce anxiety and improve performance by 40%.',
                'action': 'Schedule 2 mock interviews per week with peers or use platforms like Pramp or Interviewing.io.'
            },
            {
                'title': 'Build a Project Portfolio',
                'description': 'Having 2-3 solid projects on GitHub significantly boosts your profile.',
                'action': 'Build projects that solve real problems. Document them well with README files.'
            },
            {
                'title': 'Learn from Rejections',
                'description': 'Every rejection is a learning opportunity. Analyze what went wrong.',
                'action': 'After each interview, write down what was asked, what you struggled with, and create a study plan.'
            }
        ])
        
        return tips[:5]  # Return top 5 tips