// get the ninja-keys element
const ninja = document.querySelector('ninja-keys');

// add the home and posts menu items
ninja.data = [{
    id: "nav-about",
    title: "about",
    section: "Navigation",
    handler: () => {
      window.location.href = "/";
    },
  },{id: "nav-publications",
          title: "publications",
          description: "",
          section: "Navigation",
          handler: () => {
            window.location.href = "/publications/";
          },
        },{id: "nav-cv",
          title: "cv",
          description: "",
          section: "Navigation",
          handler: () => {
            window.location.href = "/cv/";
          },
        },{id: "nav-repositories",
          title: "repositories",
          description: "",
          section: "Navigation",
          handler: () => {
            window.location.href = "/repositories/";
          },
        },{id: "nav-teaching",
          title: "teaching",
          description: "Here is a list of courses that I have taught or TA’ed.",
          section: "Navigation",
          handler: () => {
            window.location.href = "/teaching/";
          },
        },{id: "news-i-won-the-best-new-neuromorph-award-at-the-2024-telluride-neuromorphic-cognition-engineering-workshop-along-with-mara-wolter-u-tubingen",
          title: 'I won the Best “New Neuromorph” award at the 2024 Telluride Neuromorphic Cognition...',
          description: "",
          section: "News",},{id: "news-best-paper-award-at-icann",
          title: 'Best paper award at ICANN!',
          description: "",
          section: "News",},{id: "news-i-will-defend-my-phd-dissertation-on-january-13-click-here-for-more-information",
          title: 'I will defend my PhD dissertation on January 13. Click here for more...',
          description: "",
          section: "News",},{id: "news-applications-are-open-for-the-2025-telluride-neuromorphic-cognition-engineering-workshop",
          title: 'Applications are open for the 2025 Telluride Neuromorphic Cognition Engineering Workshop',
          description: "",
          section: "News",handler: () => {
              window.location.href = "/news/announcement_1/";
            },},{
        id: 'social-email',
        title: 'email',
        section: 'Socials',
        handler: () => {
          window.open("mailto:%6E%73%32%64%75%6D%6F%6E%74@%75%77%61%74%65%72%6C%6F%6F.%63%61", "_blank");
        },
      },{
        id: 'social-github',
        title: 'GitHub',
        section: 'Socials',
        handler: () => {
          window.open("https://github.com/nsdumont", "_blank");
        },
      },{
        id: 'social-linkedin',
        title: 'LinkedIn',
        section: 'Socials',
        handler: () => {
          window.open("https://www.linkedin.com/in/nicole-dumont", "_blank");
        },
      },{
        id: 'social-orcid',
        title: 'ORCID',
        section: 'Socials',
        handler: () => {
          window.open("https://orcid.org/0000-0001-5041-1527", "_blank");
        },
      },{
        id: 'social-scholar',
        title: 'Google Scholar',
        section: 'Socials',
        handler: () => {
          window.open("https://scholar.google.com/citations?user=2hnh9gkAAAAJ", "_blank");
        },
      },{
        id: 'social-custom_social',
        title: 'Custom_social',
        section: 'Socials',
        handler: () => {
          window.open("https://compneuro.uwaterloo.ca/people/nicole-dumont.html", "_blank");
        },
      },{
      id: 'light-theme',
      title: 'Change theme to light',
      description: 'Change the theme of the site to Light',
      section: 'Theme',
      handler: () => {
        setThemeSetting("light");
      },
    },
    {
      id: 'dark-theme',
      title: 'Change theme to dark',
      description: 'Change the theme of the site to Dark',
      section: 'Theme',
      handler: () => {
        setThemeSetting("dark");
      },
    },
    {
      id: 'system-theme',
      title: 'Use system default theme',
      description: 'Change the theme of the site to System Default',
      section: 'Theme',
      handler: () => {
        setThemeSetting("system");
      },
    },];
