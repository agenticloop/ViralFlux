from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class RedditServiceError(Exception):
    """Raised when Reddit API access fails."""


class RedditService:
    """PRAW-backed Reddit service for fetching trending horror posts.

    Uses read-only (script) authentication — no user login required.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
    ) -> None:
        if not client_id or not client_secret:
            raise RedditServiceError(
                "Reddit API credentials are not set. "
                "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in your .env file."
            )

        import praw

        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        # Force read-only mode (no user auth needed)
        self.reddit.read_only = True

    def get_trending_posts(
        self,
        subreddits: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Fetch hot posts from horror subreddits.

        Returns a list of post dicts sorted by score (descending), each with:
            title, url, score, text (first 2000 chars), subreddit
        """
        subreddits = subreddits or ["nosleep", "creepypasta", "LetsNotMeet"]
        posts: list[dict] = []

        per_sub = max(1, limit // len(subreddits) + 1)

        for sub_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(sub_name)
                for post in subreddit.hot(limit=per_sub * 2):
                    if post.stickied:
                        continue
                    if len(post.selftext or "") < 200:
                        continue

                    posts.append(
                        {
                            "title": post.title,
                            "url": f"https://reddit.com{post.permalink}",
                            "score": post.score,
                            "text": post.selftext[:2000],
                            "subreddit": sub_name,
                        }
                    )

                    if len(posts) >= per_sub:
                        break

            except Exception as exc:
                logger.warning(
                    "Could not fetch posts from r/%s: %s", sub_name, exc
                )
                continue

        # Sort by score descending, return top `limit`
        posts.sort(key=lambda x: x["score"], reverse=True)
        logger.info(
            "Fetched %d trending posts from %s", len(posts[:limit]), subreddits
        )
        return posts[:limit]

    def get_post_text(self, url: str) -> str:
        """Fetch the full selftext of a Reddit post by its URL.

        Useful when get_trending_posts only captured the first 2000 chars.
        """
        try:
            submission = self.reddit.submission(url=url)
            return submission.selftext or ""
        except Exception as exc:
            raise RedditServiceError(
                f"Failed to fetch Reddit post at {url}: {exc}"
            ) from exc
