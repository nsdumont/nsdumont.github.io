---
layout: page
permalink: /teaching/
title: teaching
meta_description: "Courses taught or assisted by Nicole Dumont, including computational neuroscience and computer science courses at the University of Waterloo."
description: Courses I have taught or assisted with.
nav: true
nav_order: 5
---

<ul class="teaching">
  {% for course in site.data.teaching %}
    {% include course.liquid course=course %}
  {% endfor %}
</ul>
