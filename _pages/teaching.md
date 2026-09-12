---
layout: page
permalink: /teaching/
title: teaching
description: Courses I have taught or assisted with.
nav: true
nav_order: 5
---

<ul class="teaching">
  {% for course in site.data.teaching %}
    {% include course.liquid course=course %}
  {% endfor %}
</ul>
