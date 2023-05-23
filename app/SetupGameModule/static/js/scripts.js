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


function parseBBCode() {
      let postContents = document.getElementsByClassName("post-content");
      for (let i = 0; i < postContents.length; i++) {
        let html = postContents[i].innerHTML;

        // Zamień zagnieżdżone cytaty (quote) na odpowiednie znaczniki HTML
        let nestedQuoteRegex = /\[QUOTE\]([\s\S]*?)\[QUOTE\]([\s\S]*?)\[\/QUOTE\]([\s\S]*?)\[\/QUOTE\]/g;
        while (nestedQuoteRegex.test(html)) {
          html = html.replace(nestedQuoteRegex, '<div class="post-quote">$1<div class="post-quote">$2</div>$3</div>');
        }

        // Zamień tagi BBCode na odpowiednie znaczniki HTML
        html = html.replace(/\[B\](.*?)\[\/B\]/g, "<strong>$1</strong>");
        html = html.replace(/\[I\](.*?)\[\/I\]/g, "<em>$1</em>");
        html = html.replace(/\[U\](.*?)\[\/U\]/g, "<u>$1</u>");
        html = html.replace(/\[QUOTE\](.*?)\[\/QUOTE\]/g, '<div class="post-quote">$1</div>');
        html = html.replace(/\[URL=(.*?)\](.*?)\[\/URL\]/g, '<a href="$1">$2</a>');
        html = html.replace(/\[IMG\](.*?)\[\/IMG\]/g, '<img src="$1" alt="Obrazek">');

        // Ustaw przetworzony kod HTML w elemencie
        postContents[i].innerHTML = html + "<p>Parsing BBCode completed</p>";
      }
    }