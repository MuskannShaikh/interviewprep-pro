"""
Dashboard Module
Displays analytics and visualizations for interview tracking
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager

class Dashboard:
    """Creates and displays dashboard visualizations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def show_dashboard(self, user_id: int):
        """Display complete dashboard"""
        
        st.title("📊 Interview Analytics Dashboard")
        
        # Get data
        interviews = self.db.get_user_interviews(user_id)
        
        if not interviews:
            st.info("📋 No data available yet. Start by adding your first interview!")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(interviews)
        
        # Display metrics
        self._show_key_metrics(df, user_id)
        
        st.markdown("---")
        
        # Display charts
        col1, col2 = st.columns(2)
        
        with col1:
            self._show_status_distribution(df)
            self._show_preparation_analysis(df)
        
        with col2:
            self._show_timeline_chart(df)
            self._show_company_breakdown(df)
        
        st.markdown("---")
        
        # Success rate analysis
        self._show_success_rate_analysis(df)
    
    def _show_key_metrics(self, df: pd.DataFrame, user_id: int):
        """Display key performance indicators"""
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        total = len(df)
        applied = len(df[df['status'] == 'Applied'])
        interviewed = len(df[df['status'] == 'Interviewed'])
        selected = len(df[df['status'] == 'Selected'])
        rejected = len(df[df['status'] == 'Rejected'])
        
        with col1:
            st.metric(
                label="📝 Total Applications",
                value=total,
                delta=f"+{len(df[df['created_at'] >= (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')])} this week"
            )
        
        with col2:
            st.metric(
                label="🟡 Applied",
                value=applied
            )
        
        with col3:
            st.metric(
                label="🔵 Interviewed",
                value=interviewed
            )
        
        with col4:
            st.metric(
                label="🟢 Selected",
                value=selected,
                delta=f"{(selected/total*100):.1f}% success rate" if total > 0 else "0%"
            )
        
        with col5:
            st.metric(
                label="🔴 Rejected",
                value=rejected
            )
        
        # Average preparation level
        avg_prep = df['preparation_level'].mean()
        st.metric(
            label="⭐ Average Preparation Level",
            value=f"{avg_prep:.2f}/5.0"
        )
    
    def _show_status_distribution(self, df: pd.DataFrame):
        """Show pie chart of status distribution"""
        
        st.subheader("📈 Status Distribution")
        
        status_counts = df['status'].value_counts()
        
        colors = {
            'Applied': '#FFA500',
            'Interviewed': '#4169E1',
            'Selected': '#32CD32',
            'Rejected': '#DC143C'
        }
        
        fig = go.Figure(data=[go.Pie(
            labels=status_counts.index,
            values=status_counts.values,
            hole=0.4,
            marker=dict(colors=[colors.get(status, '#CCCCCC') for status in status_counts.index])
        )])
        
        fig.update_layout(
            height=300,
            showlegend=True,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_timeline_chart(self, df: pd.DataFrame):
        """Show timeline of interviews"""
        
        st.subheader("📅 Interview Timeline")
        
        # Group by date and status
        df['interview_date'] = pd.to_datetime(df['interview_date'])
        timeline = df.groupby(['interview_date', 'status']).size().reset_index(name='count')
        
        fig = px.line(
            timeline,
            x='interview_date',
            y='count',
            color='status',
            markers=True,
            color_discrete_map={
                'Applied': '#FFA500',
                'Interviewed': '#4169E1',
                'Selected': '#32CD32',
                'Rejected': '#DC143C'
            }
        )
        
        fig.update_layout(
            height=300,
            xaxis_title="Date",
            yaxis_title="Number of Interviews",
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_preparation_analysis(self, df: pd.DataFrame):
        """Show preparation level analysis"""
        
        st.subheader("⭐ Preparation Level Analysis")
        
        prep_counts = df['preparation_level'].value_counts().sort_index()
        
        fig = go.Figure(data=[go.Bar(
            x=prep_counts.index,
            y=prep_counts.values,
            marker_color='#4169E1',
            text=prep_counts.values,
            textposition='auto'
        )])
        
        fig.update_layout(
            height=300,
            xaxis_title="Preparation Level",
            yaxis_title="Number of Interviews",
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(tickmode='linear', tick0=1, dtick=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_company_breakdown(self, df: pd.DataFrame):
        """Show top companies"""
        
        st.subheader("🏢 Top Companies")
        
        company_counts = df['company_name'].value_counts().head(10)
        
        fig = go.Figure(data=[go.Bar(
            x=company_counts.values,
            y=company_counts.index,
            orientation='h',
            marker_color='#32CD32',
            text=company_counts.values,
            textposition='auto'
        )])
        
        fig.update_layout(
            height=300,
            xaxis_title="Number of Applications",
            yaxis_title="Company",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_success_rate_analysis(self, df: pd.DataFrame):
        """Show success rate by preparation level"""
        
        st.subheader("🎯 Success Rate by Preparation Level")
        
        # Calculate success rate for each preparation level
        success_data = []
        
        for prep_level in range(1, 6):
            prep_df = df[df['preparation_level'] == prep_level]
            total = len(prep_df)
            
            if total > 0:
                selected = len(prep_df[prep_df['status'] == 'Selected'])
                success_rate = (selected / total) * 100
                success_data.append({
                    'Preparation Level': prep_level,
                    'Success Rate (%)': success_rate,
                    'Total Interviews': total
                })
        
        if success_data:
            success_df = pd.DataFrame(success_data)
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=success_df['Preparation Level'],
                y=success_df['Success Rate (%)'],
                name='Success Rate',
                marker_color='#32CD32',
                text=success_df['Success Rate (%)'].round(1),
                texttemplate='%{text}%',
                textposition='auto'
            ))
            
            fig.add_trace(go.Scatter(
                x=success_df['Preparation Level'],
                y=success_df['Total Interviews'],
                name='Total Interviews',
                yaxis='y2',
                mode='lines+markers',
                marker_color='#4169E1',
                line=dict(width=2)
            ))
            
            fig.update_layout(
                height=350,
                xaxis_title="Preparation Level",
                yaxis_title="Success Rate (%)",
                yaxis2=dict(
                    title="Total Interviews",
                    overlaying='y',
                    side='right'
                ),
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(tickmode='linear', tick0=1, dtick=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Insights
            best_prep = success_df.loc[success_df['Success Rate (%)'].idxmax()]
            st.info(f"💡 **Insight:** Your highest success rate ({best_prep['Success Rate (%)']:.1f}%) is at preparation level {int(best_prep['Preparation Level'])}!")