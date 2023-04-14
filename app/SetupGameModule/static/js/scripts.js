var tabNav = document.querySelector('.tab-nav');
var tabNavLinks = tabNav.querySelectorAll('a');
var tabContent = document.querySelector('.tab-content');
var tabContentSections = tabContent.querySelectorAll('div');

for (var i = 0; i < tabNavLinks.length; i++) {
  tabNavLinks[i].addEventListener('click', function(e) {
    e.preventDefault();
    var currentTab = tabNav.querySelector('.active');
    currentTab.classList.remove('active');
    var currentTabSection = tabContent.querySelector('.active');
    currentTabSection.classList.remove('active');

    var newTab = this.parentNode;
    newTab.classList.add('active');
    var newTabSection = tabContent.querySelector(this.getAttribute('href'));
    newTabSection.classList.add('active');
  });
}
