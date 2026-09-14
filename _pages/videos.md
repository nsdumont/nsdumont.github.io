---
layout: page
permalink: /videos/
title: talks
meta_description: "Recorded talks and lectures by Nicole Dumont on computational neuroscience, spatial cognition, spatial semantic pointers, and spiking neural networks."
description: Recorded talks and lectures
nav: true
nav_order: 6
---

{% assign talks = site.data.talks | sort: 'date' | reverse %}

<ul class="talks">
  {% for talk in talks %}
    {% include talk.liquid talk=talk %}
  {% endfor %}
</ul>
