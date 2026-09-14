---
layout: page
permalink: /cv/
title: cv
meta_description: "Curriculum vitae of Nicole Dumont, postdoctoral researcher in computational neuroscience at the Institute of Neuroinformatics (UZH/ETH Zürich): education, research positions, publications, talks, teaching, and awards."
nav: true
nav_order: 3
description:
toc: false
---

{% assign cv = site.data.cv %}
{% assign pdf = '/assets/pdf/CV.pdf' | relative_url %}

{% if cv %}

<div class="cv-page">
  <div class="cv-top">
    <div>
      <div class="cv-name">{{ cv.name }}</div>
      {% if cv.tagline != '' %}<div class="cv-tagline">{{ cv.tagline }}</div>{% endif %}
      <div class="cv-contact">
        {% for c in cv.contact %}
          <span>{% if c.icon != '' %}<i class="{{ c.icon }}"></i>{% endif %}{{ c.html }}</span>
        {% endfor %}
      </div>
    </div>
    <a class="cv-download" href="{{ pdf }}" target="_blank" rel="noopener"><i class="fa-solid fa-file-arrow-down"></i> Download PDF</a>
  </div>

{% for section in cv.sections %}
{% if section.title != '' %}<h2 class="cv-section">{{ section.title }}</h2>{% endif %}
{% include cv/blocks.liquid blocks=section.blocks %}
{% endfor %}

</div>
{% else %}
<p>
  <a href="{{ pdf }}" target="_blank" rel="noopener">Download CV (PDF)</a>
</p>
<div style="width:100%; height:80vh;">
  <embed src="{{ pdf }}" type="application/pdf" width="100%" height="100%">
</div>
{% endif %}
