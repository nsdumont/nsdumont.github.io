---
layout: page
permalink: /repositories/
title: repositories
meta_description: "Open-source code by Nicole Dumont: software for spatial semantic pointers, vector symbolic architectures, spiking neural networks, and neurosymbolic models of spatial cognition."
description:
nav: true
nav_order: 4
---

{% if site.data.repositories.github_repos %}

<ul class="repositories">
  {% for repo in site.data.repositories.github_repos %}
    {% include repository/repo.liquid repository=repo %}
  {% endfor %}
</ul>
{% endif %}
