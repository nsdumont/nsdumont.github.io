---
layout: page
permalink: /videos/
title: talks
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
