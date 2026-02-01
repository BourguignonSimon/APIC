"""
Reusable UI components for the APIC frontend.
"""

import streamlit as st

from utils import get_status_info


def display_status_badge(status: str):
    """Display status badge with appropriate styling."""
    info = get_status_info(status)
    st.markdown(
        f'<span class="status-badge {info["class"]}">{info["label"]}</span>',
        unsafe_allow_html=True
    )


def render_empty_state(icon: str, title: str, message: str, show_button: bool = False, button_label: str = "", button_key: str = "") -> bool:
    """Render an empty state message. Returns True if button was clicked."""
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-text">{message}</div>
    </div>
    """, unsafe_allow_html=True)

    if show_button:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            return st.button(button_label, key=button_key, use_container_width=True, type="primary")
    return False


def render_info_message(message: str, icon: str = "i"):
    """Render a custom info message."""
    st.markdown(f"""
    <div class="custom-info">
        <span class="custom-info-icon">{icon}</span>
        <span class="custom-info-text">{message}</span>
    </div>
    """, unsafe_allow_html=True)


def render_success_message(message: str, icon: str = "OK"):
    """Render a custom success message."""
    st.markdown(f"""
    <div class="custom-success">
        <span class="custom-info-icon">{icon}</span>
        <span class="custom-success-text">{message}</span>
    </div>
    """, unsafe_allow_html=True)


def render_warning_message(message: str, icon: str = "!"):
    """Render a custom warning message."""
    st.markdown(f"""
    <div class="custom-warning">
        <span class="custom-info-icon">{icon}</span>
        <span class="custom-warning-text">{message}</span>
    </div>
    """, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str = ""):
    """Render a page header with optional subtitle."""
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def render_section_title(title: str):
    """Render a section title."""
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def render_metric_card(value: str, label: str, style: str = "primary"):
    """Render a metric card."""
    st.markdown(f"""
    <div class="metric-card {style}">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_feature_card(icon: str, title: str, text: str):
    """Render a feature card."""
    st.markdown(f"""
    <div class="feature-card">
        <div class="feature-card-icon">{icon}</div>
        <div class="feature-card-title">{title}</div>
        <div class="feature-card-text">{text}</div>
    </div>
    """, unsafe_allow_html=True)
