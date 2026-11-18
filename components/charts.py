"""AquaLoad Plotly figures. Inputs are existing report metrics, never estimates."""
import math
import textwrap
import plotly.graph_objects as go
import streamlit as st

TEAL, BLUE = '#009c9b', '#2784c5'

def chart_style(figure, *, height=320, integer_axis=None):
    preference = st.session_state.get('theme_preference', 'System')
    dark = preference == 'Dark'
    if preference == 'System':
        dark = getattr(getattr(st.context, 'theme', None), 'type', 'light') == 'dark'
    text, grid = ('#d6eaf2', '#294553') if dark else ('#23475c', '#e1eaf0')
    figure.update_layout(template='plotly_dark' if dark else 'plotly_white',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Arial, sans-serif', size=14, color=text),
        height=height, margin=dict(l=12,r=20,t=64,b=48),
        legend=dict(orientation='h',y=1.2,x=0,font=dict(size=13)),
        bargap=.35, bargroupgap=.06, hoverlabel=dict(font_size=14))
    figure.update_xaxes(tickangle=0, automargin=True, showgrid=False, zeroline=False)
    figure.update_yaxes(automargin=True, gridcolor=grid, zeroline=False)
    if integer_axis:
        figure.update_layout(**{integer_axis: dict(tickformat=',d',dtick=1)})
    return figure

def capacity_chart(plans):
    labels = [f"Plan #{p['plan_id']}" for p in plans]
    figure = go.Figure()
    for key,name,color in [('space_utilization','Lorry volume (%)',TEAL),('weight_utilization','Weight capacity (%)',BLUE)]:
        values = [float(p[key]) for p in plans]
        figure.add_bar(x=labels,y=values,name=name,marker_color=color,
            hovertemplate='%{x}<br>'+name+': %{y:.1f}%<extra></extra>')
    largest = max((float(p[k]) for p in plans for k in ('space_utilization','weight_utilization')), default=0)
    figure.update_layout(barmode='group',yaxis=dict(title='Capacity used (%)',range=[0,max(100,math.ceil(largest*1.12))]))
    if largest > 100:
        figure.add_hline(y=100,line_dash='dash',line_color='#c24d63',annotation_text='Capacity exceeded above this line')
    return chart_style(figure)

def bar_chart(labels, values, unit, *, horizontal=False, counts=False, color=TEAL):
    labels = [str(label) for label in labels]
    # Multi-line tick labels keep long collection point names inside mobile charts.
    display = ['<br>'.join(textwrap.wrap(label, 28)) for label in labels]
    figure = go.Figure(go.Bar(
        x=values if horizontal else labels, y=labels if horizontal else values,
        orientation='h' if horizontal else 'v',marker_color=color,width=.55,
        customdata=labels,
        hovertemplate='%{customdata}<br>%{'+('x' if horizontal else 'y')+(':.0f}' if counts else ':,.1f}')+' '+unit+'<extra></extra>'))
    axis = 'xaxis' if horizontal else 'yaxis'
    figure.update_layout(**{axis:dict(title=unit,rangemode='tozero')},showlegend=False)
    if horizontal:
        figure.update_yaxes(tickmode='array',tickvals=labels,ticktext=display,autorange='reversed',showgrid=False)
        figure.update_xaxes(showgrid=True)
    return chart_style(figure,height=max(260,min(650,70*len(labels)+80)) if horizontal else 300,integer_axis=axis if counts else None)

def render_chart(figure, key):
    st.plotly_chart(figure,width='stretch',theme=None,key=key,
        config={'displaylogo':False,'responsive':True,'scrollZoom':False,'modeBarButtonsToRemove':['lasso2d','select2d']})
