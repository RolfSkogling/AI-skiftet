<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <xsl:output method="html" encoding="UTF-8" doctype-system="about:legacy-compat" />
  <xsl:template match="/rss/channel">
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title><xsl:value-of select="title" /></title>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="crossorigin" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=Playfair+Display:wght@700;800&amp;display=swap" rel="stylesheet" />
        <link rel="stylesheet" href="/style.css" />
        <style>
          .feed-panel{max-width:920px;margin:0 0 26px;padding:16px;border:1px solid var(--line);border-radius:8px;background:var(--surface);box-shadow:var(--shadow)}
          .feed-url{display:block;margin-top:6px;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:.92rem;color:var(--muted);word-break:break-all}
          .episode-list{display:grid;gap:18px;max-width:920px}
          .episode-card{padding:22px;border:1px solid var(--line);border-radius:8px;background:var(--surface);box-shadow:var(--shadow)}
          .episode-meta{color:var(--accent);font-weight:800;letter-spacing:.06em;text-transform:uppercase;font-size:.78rem}
          .episode-card h2{margin:4px 0 8px}
          .episode-card audio{width:100%;margin-top:12px}
        </style>
      </head>
      <body>
        <nav class="site-nav">
          <div class="container-wide">
            <a href="/en/index.html" class="site-nav__logo">AI-skiftet</a>
            <div class="site-nav__links">
              <a href="/en/index.html#news">News</a>
              <a href="/en/essays.html">Essays</a>
              <a href="/en/podcasts.html">Podcasts</a>
            </div>
          </div>
        </nav>
        <section class="hero">
          <div class="container">
            <h1><xsl:value-of select="title" /></h1>
            <p class="subtitle"><xsl:value-of select="description" /></p>
          </div>
        </section>
        <section class="essays-section">
          <div class="container-wide">
            <div class="feed-panel">
              <strong>RSS feed</strong>
              <span class="feed-url">https://ai-skiftet.se/podcast.xml</span>
            </div>
            <div class="episode-list">
              <xsl:for-each select="item">
                <article class="episode-card">
                  <div class="episode-meta">Podcast episode · <xsl:value-of select="itunes:duration" /></div>
                  <h2><xsl:value-of select="title" /></h2>
                  <p><xsl:value-of select="description" /></p>
                  <audio controls="controls" preload="none">
                    <source type="audio/mp4">
                      <xsl:attribute name="src"><xsl:value-of select="enclosure/@url" /></xsl:attribute>
                    </source>
                  </audio>
                  <p><a><xsl:attribute name="href"><xsl:value-of select="link" /></xsl:attribute>Podcast page</a></p>
                </article>
              </xsl:for-each>
            </div>
          </div>
        </section>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
