const API_BASE_URL = "http://127.0.0.1:8000";

let accessToken = localStorage.getItem("access_token");

document.addEventListener("DOMContentLoaded", () => {
    updateUI();
    loadPosts();
});


function showAuth(type) {
    const authSection = document.getElementById("authSection");
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");
    const loginTab = document.getElementById("loginTab");
    const registerTab = document.getElementById("registerTab");

    authSection.classList.remove("hidden");

    if (type === "login") {
        loginForm.classList.remove("hidden");
        registerForm.classList.add("hidden");
        loginTab.classList.add("active");
        registerTab.classList.remove("active");
    } else {
        loginForm.classList.add("hidden");
        registerForm.classList.remove("hidden");
        loginTab.classList.remove("active");
        registerTab.classList.add("active");
    }

    authSection.scrollIntoView({ behavior: "smooth" });
}


async function register(event) {
    event.preventDefault();

    const username = document.getElementById("registerUsername").value;
    const email = document.getElementById("registerEmail").value;
    const password = document.getElementById("registerPassword").value;
    const message = document.getElementById("authMessage");

    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                username,
                email,
                password,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Registration failed");
        }

        message.textContent = "Registration successful! Please login.";
        message.className = "message success-message";

        document.getElementById("registerForm").reset();

        showAuth("login");

    } catch (error) {
        message.textContent = error.message;
        message.className = "message error-message";
    }
}


async function login(event) {
    event.preventDefault();

    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;
    const message = document.getElementById("authMessage");

    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                email,
                password,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Login failed");
        }

        accessToken = data.access_token;

        localStorage.setItem("access_token", accessToken);

        message.textContent = "Login successful!";
        message.className = "message success-message";

        document.getElementById("loginForm").reset();

        updateUI();

        loadPosts();

        setTimeout(() => {
            document.getElementById("authSection").classList.add("hidden");
        }, 800);

    } catch (error) {
        message.textContent = error.message;
        message.className = "message error-message";
    }
}


function logout() {
    accessToken = null;

    localStorage.removeItem("access_token");

    updateUI();

    loadPosts();

    window.scrollTo({
        top: 0,
        behavior: "smooth",
    });
}


function updateUI() {
    const loginNavButton = document.getElementById("loginNavButton");
    const registerNavButton = document.getElementById("registerNavButton");
    const logoutButton = document.getElementById("logoutButton");
    const createPostSection = document.getElementById("createPostSection");

    if (accessToken) {
        loginNavButton.classList.add("hidden");
        registerNavButton.classList.add("hidden");
        logoutButton.classList.remove("hidden");
        createPostSection.classList.remove("hidden");
    } else {
        loginNavButton.classList.remove("hidden");
        registerNavButton.classList.remove("hidden");
        logoutButton.classList.add("hidden");
        createPostSection.classList.add("hidden");
    }
}


async function loadPosts() {
    const postsContainer = document.getElementById("postsContainer");

    postsContainer.innerHTML =
        '<p class="loading">Loading posts...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/posts/`);

        const posts = await response.json();

        if (!response.ok) {
            throw new Error(
                posts.detail || "Unable to load posts"
            );
        }

        if (posts.length === 0) {
            postsContainer.innerHTML =
                '<p class="loading">No posts available yet.</p>';
            return;
        }

        postsContainer.innerHTML = "";

        posts.forEach((post) => {
            const postCard = createPostCard(post);

            postsContainer.appendChild(postCard);
        });

    } catch (error) {
        postsContainer.innerHTML =
            `<p class="message error-message">${error.message}</p>`;
    }
}


function createPostCard(post) {
    const card = document.createElement("article");

    card.className = "post-card";

    card.innerHTML = `
        <p class="eyebrow">BLOG POST</p>

        <h3>${escapeHtml(post.title)}</h3>

        <p class="post-content">
            ${escapeHtml(post.content)}
        </p>

        <p class="post-meta">
            Author ID: ${post.author_id} ·
            ${formatDate(post.created_at)}
        </p>

        <div class="post-actions">

            <button onclick="viewComments(${post.id})">
                💬 Comments
            </button>

            ${
                accessToken
                    ? `
                        <button onclick="likePost(${post.id})">
                            👍 Like
                        </button>

                        <button onclick="unlikePost(${post.id})">
                            👎 Unlike
                        </button>
                    `
                    : ""
            }

        </div>

        ${
            accessToken
                ? `
                    <div class="comment-form">
                        <textarea
                            id="comment-input-${post.id}"
                            placeholder="Write a comment..."
                            rows="3"
                        ></textarea>

                        <button
                            class="comment-submit-button"
                            onclick="addComment(${post.id})"
                        >
                            Add Comment
                        </button>
                    </div>
                `
                : ""
        }

        <div
            id="comments-${post.id}"
            class="comments-container"
        ></div>
    `;

    return card;
}


async function createPost(event) {
    event.preventDefault();

    const title =
        document.getElementById("postTitle").value;

    const content =
        document.getElementById("postContent").value;

    const message =
        document.getElementById("postMessage");

    try {
        const response = await fetch(
            `${API_BASE_URL}/posts/`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${accessToken}`,
                },
                body: JSON.stringify({
                    title,
                    content,
                }),
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Unable to create post"
            );
        }

        message.textContent =
            "Post published successfully!";

        message.className =
            "message success-message";

        document.getElementById("createPostForm").reset();

        loadPosts();

    } catch (error) {
        message.textContent = error.message;

        message.className =
            "message error-message";
    }
}


async function addComment(postId) {
    if (!accessToken) {
        alert("Please login to add a comment.");
        return;
    }

    const commentInput =
        document.getElementById(
            `comment-input-${postId}`
        );

    const text = commentInput.value.trim();

    if (!text) {
        alert("Please enter a comment.");
        return;
    }

    try {
        const response = await fetch(
            `${API_BASE_URL}/posts/${postId}/comments/`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${accessToken}`,
                },
                body: JSON.stringify({
                    text,
                }),
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Unable to add comment"
            );
        }

        commentInput.value = "";

        alert("Comment added successfully!");

        viewComments(postId);

    } catch (error) {
        alert(error.message);
    }
}


async function likePost(postId) {
    if (!accessToken) {
        alert("Please login to like a post.");
        return;
    }

    try {
        const response = await fetch(
            `${API_BASE_URL}/posts/${postId}/likes/`,
            {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${accessToken}`,
                },
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Unable to like post"
            );
        }

        alert(data.message);

    } catch (error) {
        alert(error.message);
    }
}


async function unlikePost(postId) {
    if (!accessToken) {
        alert("Please login to unlike a post.");
        return;
    }

    try {
        const response = await fetch(
            `${API_BASE_URL}/posts/${postId}/likes/`,
            {
                method: "DELETE",
                headers: {
                    "Authorization": `Bearer ${accessToken}`,
                },
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Unable to unlike post"
            );
        }

        alert(data.message);

    } catch (error) {
        alert(error.message);
    }
}


async function viewComments(postId) {
    const commentsContainer =
        document.getElementById(
            `comments-${postId}`
        );

    commentsContainer.innerHTML =
        "<p>Loading comments...</p>";

    try {
        const response = await fetch(
            `${API_BASE_URL}/posts/${postId}/comments/`
        );

        const comments = await response.json();

        if (!response.ok) {
            throw new Error(
                comments.detail ||
                "Unable to load comments"
            );
        }

        if (comments.length === 0) {
            commentsContainer.innerHTML =
                "<p>No comments yet.</p>";

            return;
        }

        commentsContainer.innerHTML =
            comments.map(
                (comment) => `
                    <div class="comment">

                        <strong>
                            User ${comment.user_id}
                        </strong>

                        <p>
                            ${escapeHtml(comment.text)}
                        </p>

                        <small>
                            ${formatDate(comment.created_at)}
                        </small>

                    </div>
                `
            ).join("");

    } catch (error) {
        commentsContainer.innerHTML =
            `<p class="error-message">${error.message}</p>`;
    }
}


function formatDate(dateString) {
    return new Date(dateString).toLocaleString();
}


function escapeHtml(value) {
    const div = document.createElement("div");

    div.textContent = value;

    return div.innerHTML;
}