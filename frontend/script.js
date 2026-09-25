const API_BASE_URL = "http://127.0.0.1:8000";

let accessToken = localStorage.getItem("access_token");

function processAuth0Callback() {
    const hash = window.location.hash;

    if (!hash || !hash.startsWith("#")) {
        return null;
    }

    const hashParams = new URLSearchParams(
        hash.substring(1)
    );

    const authToken =
        hashParams.get("auth_token");

    const authError =
        hashParams.get("auth_error");

    if (authToken) {
        accessToken = authToken;

        localStorage.setItem(
            "access_token",
            accessToken
        );

        window.history.replaceState(
            {},
            document.title,
            window.location.pathname +
                window.location.search
        );

        return "success";
    }

    if (authError) {
        const message =
            decodeURIComponent(authError);

        window.history.replaceState(
            {},
            document.title,
            window.location.pathname +
                window.location.search
        );

        const authMessage =
            document.getElementById(
                "authMessage"
            );

        if (authMessage) {
            authMessage.textContent =
                message;

            authMessage.className =
                "message error-message";
        }

        return "error";
    }

    return null;
}
let currentUserId = null;

let maxImagesPerPost = 1;
let subscriptionPlanName = "";
let subscriptionPlans = [];
let currentSubscriptionPlanId = null;

let selectedCreateImages = [];
let selectedEditImages = [];

let editingPost = null;

let postAnalyticsChart = null;
let activityChart = null;

let notificationPollingInterval = null;
let notificationDropdownOpen = false;


document.addEventListener("DOMContentLoaded", async () => {
    processAuth0Callback();

    updateUI();

    if (accessToken) {
        await loadSubscriptionLimits();
        await loadSubscriptionPlans();
        await loadDashboard();
        await loadNotifications();
        startNotificationPolling();
    }

    await loadPosts();
});


async function register(event) {
    event.preventDefault();

    const username =
        document.getElementById("registerUsername").value.trim();

    const email =
        document.getElementById("registerEmail").value.trim();

    const password =
        document.getElementById("registerPassword").value;

    const message =
        document.getElementById("authMessage");

    try {
        const response = await fetch(
            `${API_BASE_URL}/auth/signup/`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    username,
                    email,
                    password,
                }),
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Registration failed"
            );
        }

        message.textContent =
            "Registration successful! Please login.";

        message.className =
            "message success-message";

        document
            .getElementById("registerForm")
            .reset();

        showAuth("login");

    } catch (error) {
        message.textContent =
            error.message;

        message.className =
            "message error-message";
    }
}


async function login(event) {
    event.preventDefault();

    const email =
        document.getElementById("loginEmail").value.trim();

    const password =
        document.getElementById("loginPassword").value;

    const message =
        document.getElementById("authMessage");

    try {
        const response = await fetch(
            `${API_BASE_URL}/auth/login`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    email,
                    password,
                }),
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Login failed"
            );
        }

        accessToken =
            data.access_token;

        localStorage.setItem(
            "access_token",
            accessToken
        );

        message.textContent =
            "Login successful!";

        message.className =
            "message success-message";

        document
            .getElementById("loginForm")
            .reset();

        updateUI();

        await loadSubscriptionLimits();
        await loadSubscriptionPlans();
        await loadDashboard();
        await loadNotifications();

        startNotificationPolling();

        await loadPosts();

        setTimeout(() => {
            document
                .getElementById("authSection")
                .classList.add("hidden");
        }, 800);

    } catch (error) {
        message.textContent =
            error.message;

        message.className =
            "message error-message";
    }
}


function logout() {
    stopNotificationPolling();

    accessToken = null;
    currentUserId = null;
    subscriptionPlanName = "";
    subscriptionPlans = [];
    currentSubscriptionPlanId = null;
    maxImagesPerPost = 1;

    localStorage.removeItem("access_token");

    closeNotificationDropdown();

    updateUI();

    document
        .getElementById("dashboardSection")
        .classList.add("hidden");

    document
        .getElementById("editPostSection")
        .classList.add("hidden");

    loadPosts();

    window.scrollTo({
        top: 0,
        behavior: "smooth",
    });
}


function showAuth(type) {
    const authSection =
        document.getElementById("authSection");

    const loginForm =
        document.getElementById("loginForm");

    const registerForm =
        document.getElementById("registerForm");

    const loginTab =
        document.getElementById("loginTab");

    const registerTab =
        document.getElementById("registerTab");

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

    authSection.scrollIntoView({
        behavior: "smooth",
    });
}


function updateUI() {
    const loginNavButton =
        document.getElementById("loginNavButton");

    const registerNavButton =
        document.getElementById("registerNavButton");

    const dashboardNavButton =
        document.getElementById("dashboardNavButton");

    const logoutButton =
        document.getElementById("logoutButton");

    const notificationCenter =
        document.getElementById("notificationCenter");

    const createPostSection =
        document.getElementById("createPostSection");

    if (accessToken) {
        loginNavButton.classList.add("hidden");
        registerNavButton.classList.add("hidden");
        dashboardNavButton.classList.remove("hidden");
        logoutButton.classList.remove("hidden");
        createPostSection.classList.remove("hidden");

        notificationCenter.classList.remove("hidden");
    } else {
        loginNavButton.classList.remove("hidden");
        registerNavButton.classList.remove("hidden");
        dashboardNavButton.classList.add("hidden");
        logoutButton.classList.add("hidden");
        createPostSection.classList.add("hidden");

        notificationCenter.classList.add("hidden");
    }

    updateAISupportVisibility();

    updateImageInputMode(
        document.getElementById("createPostImages")
    );

    updateImageInputMode(
        document.getElementById("editPostImages")
    );
}


async function loadSubscriptionLimits() {
    if (!accessToken) {
        return;
    }

    try {
        const response = await fetch(
            `${API_BASE_URL}/posts/limits`,
            {
                headers: {
                    "Authorization":
                        `Bearer ${accessToken}`,
                },
            }
        );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to load subscription limits"
            );
        }

        subscriptionPlanName =
            data.plan_name || "";

        maxImagesPerPost =
            data.max_images_per_post === null
                ? Infinity
                : Number(data.max_images_per_post);

        updateImageInputMode(
            document.getElementById("createPostImages")
        );

        updateImageInputMode(
            document.getElementById("editPostImages")
        );

        updateImageLimitHints();

    } catch (error) {
        console.error(error);

        maxImagesPerPost = 1;

        updateImageInputMode(
            document.getElementById("createPostImages")
        );

        updateImageInputMode(
            document.getElementById("editPostImages")
        );

        updateImageLimitHints();
    }
}




async function loadSubscriptionPlans() {
    const container =
        document.getElementById(
            "subscriptionPlansContainer"
        );

    if (!container) {
        return;
    }

    if (!accessToken) {
        container.innerHTML =
            '<p class="loading">Please login to view subscription plans.</p>';
        return;
    }

    const message =
        document.getElementById(
            "subscriptionMessage"
        );

    container.innerHTML =
        '<p class="loading">Loading subscription plans...</p>';

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/subscriptions/plans`
            );

        const plans =
            await response.json();

        if (!response.ok) {
            throw new Error(
                plans.detail ||
                "Unable to load subscription plans"
            );
        }

        subscriptionPlans =
            Array.isArray(plans)
                ? plans
                : [];

        currentSubscriptionPlanId = null;

        try {
            const currentResponse =
                await fetch(
                    `${API_BASE_URL}/subscriptions/current`,
                    {
                        headers: {
                            "Authorization":
                                `Bearer ${accessToken}`,
                        },
                    }
                );

            if (currentResponse.ok) {
                const currentPlan =
                    await currentResponse.json();

                currentSubscriptionPlanId =
                    currentPlan.id ?? null;
            }
        } catch (error) {
            console.error(
                "Current subscription error:",
                error
            );
        }

        if (subscriptionPlans.length === 0) {
            container.innerHTML =
                '<p class="loading">No subscription plans available.</p>';
            return;
        }

        container.innerHTML =
            subscriptionPlans.map(
                (plan) => {
                    const isCurrent =
                        currentSubscriptionPlanId !== null &&
                        Number(plan.id) ===
                        Number(currentSubscriptionPlanId);

                    const imageLimit =
                        plan.max_images_per_post === null
                            ? "Unlimited"
                            : plan.max_images_per_post;

                    const price =
                        plan.price === null ||
                        plan.price === undefined
                            ? "Price not available"
                            : `₹${Number(plan.price).toLocaleString("en-IN")}`;

                    return `
                        <div class="stat-card">

                            <p class="stat-label">
                                ${escapeHtml(
                                    plan.name ||
                                    "Subscription Plan"
                                )}
                            </p>

                            <h3>
                                ${escapeHtml(price)}
                            </h3>

                            <p>
                                ${
                                    imageLimit === "Unlimited"
                                        ? "Unlimited images per post"
                                        : `${imageLimit} image${Number(imageLimit) === 1 ? "" : "s"} per post`
                                }
                            </p>

                            <button
                                type="button"
                                class="${
                                    isCurrent
                                        ? "secondary-button"
                                        : "primary-button"
                                }"
                                onclick="subscribeToPlan(${Number(plan.id)})"
                                ${
                                    isCurrent
                                        ? "disabled"
                                        : ""
                                }
                            >
                                ${
                                    isCurrent
                                        ? "Current Plan"
                                        : "Choose Plan"
                                }
                            </button>

                        </div>
                    `;
                }
            ).join("");

        if (message) {
            message.textContent = "";
            message.className = "message";
        }

    } catch (error) {
        container.innerHTML =
            `<p class="message error-message">${escapeHtml(
                error.message
            )}</p>`;
    }
}


async function subscribeToPlan(planId) {
    if (!accessToken) {
        alert(
            "Please login to manage your subscription."
        );
        return;
    }

    if (
        !confirm(
            "Are you sure you want to activate this subscription plan?"
        )
    ) {
        return;
    }

    const message =
        document.getElementById(
            "subscriptionMessage"
        );

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/subscriptions/${planId}`,
                {
                    method: "POST",

                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`,
                    },
                }
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to activate subscription"
            );
        }

        if (message) {
            message.textContent =
                data.message ||
                "Subscription activated successfully.";

            message.className =
                "message success-message";
        }

        await loadSubscriptionLimits();
        await loadSubscriptionPlans();
        await loadDashboard();
        updateImageLimitHints();

    } catch (error) {
        if (message) {
            message.textContent =
                error.message;

            message.className =
                "message error-message";
        }
    }
}


function updateImageInputMode(input) {
    if (!input) {
        return;
    }

    if (maxImagesPerPost === 1) {
        input.removeAttribute("multiple");
    } else {
        input.setAttribute("multiple", "multiple");
    }
}


function updateImageLimitHints() {
    const createHint =
        document.getElementById("createImageLimitHint");

    const editHint =
        document.getElementById("editImageLimitHint");

    const limitText =
        maxImagesPerPost === Infinity
            ? "Unlimited"
            : maxImagesPerPost;

    const planText =
        subscriptionPlanName
            ? `${subscriptionPlanName} plan`
            : "Current plan";

    if (createHint) {
        createHint.textContent =
            `${planText}: up to ${limitText} image${limitText === 1 ? "" : "s"} per post.`;
    }

    if (editHint) {
        const existingCount =
            editingPost?.images?.length || 0;

        const remaining =
            maxImagesPerPost === Infinity
                ? "unlimited"
                : Math.max(
                    0,
                    maxImagesPerPost - existingCount
                );

        editHint.textContent =
            `Current images: ${existingCount}. You can add ${remaining} more image${remaining === 1 ? "" : "s"}.`;
    }
}


function showDashboard() {
    if (!accessToken) {
        alert("Please login to view your dashboard.");
        return;
    }

    const dashboardSection =
        document.getElementById("dashboardSection");

    dashboardSection.classList.remove("hidden");

    loadDashboard();

    dashboardSection.scrollIntoView({
        behavior: "smooth",
    });
}


async function loadDashboard() {
    if (!accessToken) {
        return;
    }

    const message =
        document.getElementById("dashboardMessage");

    try {
        message.textContent =
            "Loading dashboard...";

        message.className =
            "message";

        const response = await fetch(
            `${API_BASE_URL}/dashboard/`,
            {
                headers: {
                    "Authorization":
                        `Bearer ${accessToken}`,
                },
            }
        );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to load dashboard"
            );
        }

        currentUserId =
            data.user_id;

        document.getElementById(
            "dashboardUsername"
        ).textContent =
            `Welcome, ${data.username}`;

        document.getElementById(
            "totalPosts"
        ).textContent =
            data.total_posts;

        document.getElementById(
            "totalCommentsReceived"
        ).textContent =
            data.total_comments_received;

        document.getElementById(
            "totalLikesReceived"
        ).textContent =
            data.total_likes_received;

        document.getElementById(
            "totalUnlikesReceived"
        ).textContent =
            data.total_unlikes_received;

        document.getElementById(
            "totalCommentsGiven"
        ).textContent =
            data.total_comments;

        document.getElementById(
            "totalLikesGiven"
        ).textContent =
            data.total_likes_given;

        document.getElementById(
            "totalUnlikesGiven"
        ).textContent =
            data.total_unlikes_given;

        createPostAnalyticsChart(
            data.post_analytics
        );

        createActivityChart(
            data.activity
        );

        updateImageLimitHints();

        message.textContent =
            "Dashboard updated successfully.";

        message.className =
            "message success-message";

    } catch (error) {
        message.textContent =
            error.message;

        message.className =
            "message error-message";
    }
}


function createPostAnalyticsChart(postAnalytics) {
    const canvas =
        document.getElementById("postAnalyticsChart");

    if (!canvas) {
        return;
    }

    if (postAnalyticsChart) {
        postAnalyticsChart.destroy();
    }

    const labels =
        postAnalytics.map(
            (post) => post.title
        );

    const likes =
        postAnalytics.map(
            (post) => post.likes
        );

    const comments =
        postAnalytics.map(
            (post) => post.comments
        );

    const unlikes =
        postAnalytics.map(
            (post) => post.unlikes
        );

    postAnalyticsChart =
        new Chart(
            canvas,
            {
                type: "bar",

                data: {
                    labels,

                    datasets: [
                        {
                            label: "Likes Received",
                            data: likes,
                        },
                        {
                            label: "Comments Received",
                            data: comments,
                        },
                        {
                            label: "Unlikes Received",
                            data: unlikes,
                        },
                    ],
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    scales: {
                        y: {
                            beginAtZero: true,

                            ticks: {
                                precision: 0,
                            },
                        },
                    },
                },
            }
        );
}


function createActivityChart(activity) {
    const canvas =
        document.getElementById("activityChart");

    if (!canvas) {
        return;
    }

    if (activityChart) {
        activityChart.destroy();
    }

    const labels =
        activity.map(
            (item) => item.date
        );

    const datasets = [
        {
            label: "Posts Created",
            data: activity.map(
                (item) => item.posts
            ),
            tension: 0.3,
        },
        {
            label: "Comments Given",
            data: activity.map(
                (item) => item.comments_given
            ),
            tension: 0.3,
        },
        {
            label: "Comments Received",
            data: activity.map(
                (item) => item.comments_received
            ),
            tension: 0.3,
        },
        {
            label: "Likes Given",
            data: activity.map(
                (item) => item.likes_given
            ),
            tension: 0.3,
        },
        {
            label: "Likes Received",
            data: activity.map(
                (item) => item.likes_received
            ),
            tension: 0.3,
        },
        {
            label: "Unlikes Given",
            data: activity.map(
                (item) => item.unlikes_given
            ),
            tension: 0.3,
        },
        {
            label: "Unlikes Received",
            data: activity.map(
                (item) => item.unlikes_received
            ),
            tension: 0.3,
        },
    ];

    activityChart =
        new Chart(
            canvas,
            {
                type: "line",

                data: {
                    labels,
                    datasets,
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    interaction: {
                        mode: "index",
                        intersect: false,
                    },

                    scales: {
                        y: {
                            beginAtZero: true,

                            ticks: {
                                precision: 0,
                            },
                        },
                    },
                },
            }
        );
}


async function loadPosts() {
    await loadPostList(
        `${API_BASE_URL}/posts/`,
        "Latest Posts",
        false
    );
}


async function showMyPosts() {
    if (!accessToken) {
        alert("Please login to view your posts.");
        return;
    }

    await loadPostList(
        `${API_BASE_URL}/posts/mine`,
        "My Posts",
        true
    );

    document
        .getElementById("postsSection")
        .scrollIntoView({
            behavior: "smooth",
        });
}


async function loadPostList(
    url,
    heading,
    myPostsMode
) {
    const postsContainer =
        document.getElementById("postsContainer");

    const postsHeading =
        document.getElementById("postsHeading");

    const showAllButton =
        document.getElementById("showAllPostsButton");

    postsHeading.textContent =
        heading;

    if (myPostsMode) {
        showAllButton.classList.remove("hidden");
    } else {
        showAllButton.classList.add("hidden");
    }

    postsContainer.innerHTML =
        '<p class="loading">Loading posts...</p>';

    try {
        const response =
            await fetch(
                url,
                accessToken
                    ? {
                        headers: {
                            "Authorization":
                                `Bearer ${accessToken}`,
                        },
                    }
                    : {}
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to load posts"
            );
        }

        const posts =
            Array.isArray(data)
                ? data
                : data.posts || [];

        if (posts.length === 0) {
            postsContainer.innerHTML =
                '<p class="loading">No posts available.</p>';

            return;
        }

        postsContainer.innerHTML = "";

        posts.forEach((post) => {
            postsContainer.appendChild(
                createPostCard(post)
            );
        });

    } catch (error) {
        postsContainer.innerHTML =
            `<p class="message error-message">${escapeHtml(
                error.message
            )}</p>`;
    }
}


function getPostImages(post) {
    const imagePaths = [];

    if (post.image) {
        imagePaths.push({
            id: null,
            path: post.image,
        });
    }

    if (Array.isArray(post.images)) {
        post.images.forEach((image) => {
            if (
                image &&
                image.image_path &&
                !imagePaths.some(
                    (item) =>
                        item.path === image.image_path
                )
            ) {
                imagePaths.push({
                    id: image.id,
                    path: image.image_path,
                });
            } else if (
                image &&
                image.image_path
            ) {
                const existing =
                    imagePaths.find(
                        (item) =>
                            item.path === image.image_path
                    );

                if (
                    existing &&
                    existing.id === null
                ) {
                    existing.id = image.id;
                }
            }
        });
    }

    return imagePaths;
}


function createPostCarousel(
    post,
    isOwner
) {
    const images =
        getPostImages(post);

    if (images.length === 0) {
        return "";
    }

    const carouselId =
        `carousel-${post.id}`;

    const slides =
        images.map(
            (image, index) => `
                <div class="carousel-slide">
                    <img
                        src="${getMediaUrl(image.path)}"
                        alt="${escapeHtml(post.title)} image ${index + 1}"
                        class="post-image"
                        loading="lazy"
                    >
                </div>
            `
        ).join("");

    const dots =
        images.map(
            (_, index) => `
                <button
                    type="button"
                    class="carousel-dot ${index === 0 ? "active" : ""}"
                    onclick="goToCarouselSlide('${carouselId}', ${index})"
                    aria-label="Go to image ${index + 1}"
                ></button>
            `
        ).join("");

    return `
        <div
            class="post-carousel"
            id="${carouselId}"
        >

            <div
                class="carousel-track"
                onscroll="updateCarouselState('${carouselId}')"
            >
                ${slides}
            </div>

            ${
                images.length > 1
                    ? `
                        <button
                            type="button"
                            class="carousel-arrow carousel-prev"
                            onclick="moveCarousel('${carouselId}', -1)"
                            aria-label="Previous image"
                        >
                            ‹
                        </button>

                        <button
                            type="button"
                            class="carousel-arrow carousel-next"
                            onclick="moveCarousel('${carouselId}', 1)"
                            aria-label="Next image"
                        >
                            ›
                        </button>

                        <div class="carousel-dots">
                            ${dots}
                        </div>

                        <span class="carousel-count">
                            1 / ${images.length}
                        </span>
                    `
                    : ""
            }

        </div>
    `;
}


function setupCarousel(carouselId) {
    updateCarouselState(carouselId);
}


function getCarouselElements(carouselId) {
    const carousel =
        document.getElementById(carouselId);

    if (!carousel) {
        return null;
    }

    const track =
        carousel.querySelector(".carousel-track");

    const slides =
        carousel.querySelectorAll(".carousel-slide");

    const dots =
        carousel.querySelectorAll(".carousel-dot");

    const counter =
        carousel.querySelector(".carousel-count");

    return {
        carousel,
        track,
        slides,
        dots,
        counter,
    };
}


function updateCarouselState(carouselId) {
    const elements =
        getCarouselElements(carouselId);

    if (!elements) {
        return;
    }

    const {
        track,
        slides,
        dots,
        counter,
    } = elements;

    if (!track || slides.length === 0) {
        return;
    }

    const index =
        Math.min(
            slides.length - 1,
            Math.max(
                0,
                Math.round(
                    track.scrollLeft /
                    track.clientWidth
                )
            )
        );

    dots.forEach(
        (dot, dotIndex) => {
            dot.classList.toggle(
                "active",
                dotIndex === index
            );
        }
    );

    if (counter) {
        counter.textContent =
            `${index + 1} / ${slides.length}`;
    }
}


function moveCarousel(
    carouselId,
    direction
) {
    const elements =
        getCarouselElements(carouselId);

    if (!elements || !elements.track) {
        return;
    }

    elements.track.scrollBy({
        left:
            elements.track.clientWidth *
            direction,
        behavior: "smooth",
    });
}


function goToCarouselSlide(
    carouselId,
    index
) {
    const elements =
        getCarouselElements(carouselId);

    if (!elements || !elements.track) {
        return;
    }

    elements.track.scrollTo({
        left:
            elements.track.clientWidth *
            index,
        behavior: "smooth",
    });
}


function createPostCard(post) {
    const card =
        document.createElement("article");

    card.className =
        "post-card";

    const isOwner =
        accessToken &&
        currentUserId !== null &&
        Number(post.author_id) ===
            Number(currentUserId);

    card.innerHTML = `
        <p class="eyebrow">
            ${isOwner ? "MY BLOG POST" : "BLOG POST"}
        </p>

        <h3>
            ${escapeHtml(post.title)}
        </h3>

        ${createPostCarousel(
            post,
            isOwner
        )}

        <p class="post-content">
            ${escapeHtml(post.content)}
        </p>

        <p class="post-meta">
            Author ID: ${post.author_id} ·
            ${formatDate(post.created_at)}
        </p>

        <div class="post-actions">

            <button
                onclick="viewComments(${post.id})"
            >
                💬 Comments
            </button>

            ${
                accessToken
                    ? `
                        <button
                            onclick="likePost(${post.id})"
                        >
                            👍 Like
                        </button>

                        <button
                            onclick="unlikePost(${post.id})"
                        >
                            👎 Unlike
                        </button>
                    `
                    : ""
            }

            ${
                isOwner
                    ? `
                        <button
                            class="edit-button"
                            onclick="editPost(${post.id})"
                        >
                            ✏️ Edit
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

    setTimeout(
        () =>
            setupCarousel(
                `carousel-${post.id}`
            ),
        0
    );

    return card;
}


async function createPost(event) {
    event.preventDefault();

    if (!accessToken) {
        return;
    }

    const title =
        document.getElementById(
            "postTitle"
        ).value.trim();

    const content =
        document.getElementById(
            "postContent"
        ).value.trim();

    const message =
        document.getElementById(
            "postMessage"
        );

    try {
        const formData =
            new FormData();

        formData.append(
            "title",
            title
        );

        formData.append(
            "content",
            content
        );

        selectedCreateImages.forEach(
            (file) => {
                formData.append(
                    "images",
                    file
                );
            }
        );

        const response =
            await fetch(
                `${API_BASE_URL}/posts/`,
                {
                    method: "POST",

                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`,
                    },

                    body: formData,
                }
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to create post"
            );
        }

        message.textContent =
            "Post published successfully!";

        message.className =
            "message success-message";

        document
            .getElementById("createPostForm")
            .reset();

        selectedCreateImages = [];

        updateCreateImageSelection();

        await loadPosts();
        await loadDashboard();

    } catch (error) {
        message.textContent =
            error.message;

        message.className =
            "message error-message";
    }
}


function handleCreateImageSelection(event) {
    const files =
        Array.from(
            event.target.files || []
        );

    selectedCreateImages =
        limitSelectedFiles(files);

    updateCreateImageSelection();
}


function limitSelectedFiles(files) {
    if (maxImagesPerPost === Infinity) {
        return files;
    }

    return files.slice(
        0,
        maxImagesPerPost
    );
}


function updateCreateImageSelection() {
    const message =
        document.getElementById(
            "createImageSelection"
        );

    if (!message) {
        return;
    }

    if (selectedCreateImages.length === 0) {
        message.textContent =
            "No images selected.";
        return;
    }

    message.textContent =
        `Selected ${selectedCreateImages.length} image${selectedCreateImages.length === 1 ? "" : "s"}: ${
            selectedCreateImages
                .map((file) => file.name)
                .join(", ")
        }`;
}


async function editPost(postId) {
    if (!accessToken) {
        return;
    }

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/posts/${postId}`,
                {
                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`,
                    },
                }
            );

        const post =
            await response.json();

        if (!response.ok) {
            throw new Error(
                post.detail ||
                "Unable to load post"
            );
        }

        if (
            Number(post.author_id) !==
            Number(currentUserId)
        ) {
            throw new Error(
                "You can only edit your own posts."
            );
        }

        editingPost = post;

        document.getElementById(
            "editPostId"
        ).value = post.id;

        document.getElementById(
            "editPostTitle"
        ).value = post.title;

        document.getElementById(
            "editPostContent"
        ).value = post.content;

        selectedEditImages = [];

        document.getElementById(
            "editPostImages"
        ).value = "";

        renderEditImages(post);

        updateImageLimitHints();
        updateEditImageSelection();

        const section =
            document.getElementById(
                "editPostSection"
            );

        section.classList.remove("hidden");

        section.scrollIntoView({
            behavior: "smooth",
        });

    } catch (error) {
        alert(error.message);
    }
}


function renderEditImages(post) {
    const container =
        document.getElementById(
            "editImagesContainer"
        );

    const images =
        getPostImages(post);

    if (images.length === 0) {
        container.innerHTML =
            '<p class="loading">This post has no images.</p>';
        return;
    }

    const slides =
        images.map(
            (image, index) => `
                <div class="carousel-slide edit-carousel-slide">

                    <div class="edit-image-wrapper">

                        <img
                            src="${getMediaUrl(image.path)}"
                            alt="${escapeHtml(post.title)} image ${index + 1}"
                            class="post-image"
                        >

                        <button
                            type="button"
                            class="delete-image-button"
                            onclick="deletePostImage(${post.id}, ${image.id ?? 0})"
                        >
                            Delete Image
                        </button>

                    </div>

                </div>
            `
        ).join("");

    const dots =
        images.map(
            (_, index) => `
                <button
                    type="button"
                    class="carousel-dot ${index === 0 ? "active" : ""}"
                    onclick="goToCarouselSlide('edit-carousel', ${index})"
                    aria-label="Go to image ${index + 1}"
                ></button>
            `
        ).join("");

    container.innerHTML = `
        <div
            class="post-carousel edit-carousel"
            id="edit-carousel"
        >

            <div
                class="carousel-track"
                onscroll="updateCarouselState('edit-carousel')"
            >
                ${slides}
            </div>

            ${
                images.length > 1
                    ? `
                        <button
                            type="button"
                            class="carousel-arrow carousel-prev"
                            onclick="moveCarousel('edit-carousel', -1)"
                        >
                            ‹
                        </button>

                        <button
                            type="button"
                            class="carousel-arrow carousel-next"
                            onclick="moveCarousel('edit-carousel', 1)"
                        >
                            ›
                        </button>

                        <div class="carousel-dots">
                            ${dots}
                        </div>

                        <span class="carousel-count">
                            1 / ${images.length}
                        </span>
                    `
                    : ""
            }

        </div>
    `;

    setTimeout(
        () =>
            setupCarousel(
                "edit-carousel"
            ),
        0
    );
}


function handleEditImageSelection(event) {
    const files =
        Array.from(
            event.target.files || []
        );

    const currentCount =
        getPostImages(editingPost || {}).length;

    const remaining =
        maxImagesPerPost === Infinity
            ? Infinity
            : Math.max(
                0,
                maxImagesPerPost -
                currentCount
            );

    selectedEditImages =
        remaining === Infinity
            ? files
            : files.slice(
                0,
                remaining
            );

    updateEditImageSelection();
}


function updateEditImageSelection() {
    const message =
        document.getElementById(
            "editImageSelection"
        );

    if (!message) {
        return;
    }

    if (selectedEditImages.length === 0) {
        message.textContent =
            "No new images selected.";
        return;
    }

    message.textContent =
        `New images selected: ${
            selectedEditImages
                .map((file) => file.name)
                .join(", ")
        }`;
}


async function updatePost(event) {
    event.preventDefault();

    const postId =
        document.getElementById(
            "editPostId"
        ).value;

    const title =
        document.getElementById(
            "editPostTitle"
        ).value.trim();

    const content =
        document.getElementById(
            "editPostContent"
        ).value.trim();

    const message =
        document.getElementById(
            "editPostMessage"
        );

    try {
        const formData =
            new FormData();

        formData.append(
            "title",
            title
        );

        formData.append(
            "content",
            content
        );

        const response =
            await fetch(
                `${API_BASE_URL}/posts/${postId}`,
                {
                    method: "PUT",

                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`,
                    },

                    body: formData,
                }
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to update post"
            );
        }

        if (selectedEditImages.length > 0) {
            const imageFormData =
                new FormData();

            selectedEditImages.forEach(
                (file) => {
                    imageFormData.append(
                        "images",
                        file
                    );
                }
            );

            const imageResponse =
                await fetch(
                    `${API_BASE_URL}/posts/${postId}/images`,
                    {
                        method: "POST",

                        headers: {
                            "Authorization":
                                `Bearer ${accessToken}`,
                        },

                        body: imageFormData,
                    }
                );

            const imageData =
                await imageResponse.json();

            if (!imageResponse.ok) {
                throw new Error(
                    imageData.detail ||
                    "Unable to add images"
                );
            }
        }

        message.textContent =
            "Post updated successfully.";

        message.className =
            "message success-message";

        selectedEditImages = [];

        await loadPosts();

        if (
            document
                .getElementById("showAllPostsButton")
                .classList.contains("hidden") === false
        ) {
            await showMyPosts();
        }

        await loadDashboard();

        const updatedResponse =
            await fetch(
                `${API_BASE_URL}/posts/${postId}`,
                {
                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`,
                    },
                }
            );

        editingPost =
            await updatedResponse.json();

        renderEditImages(editingPost);

        updateImageLimitHints();
        updateEditImageSelection();

    } catch (error) {
        message.textContent =
            error.message;

        message.className =
            "message error-message";
    }
}




async function deletePost() {
    if (!accessToken) {
        alert("Please login to delete a post.");
        return;
    }

    const postId =
        Number(
            document.getElementById(
                "editPostId"
            ).value
        );

    if (!postId) {
        alert("No post selected.");
        return;
    }

    if (
        !confirm(
            "Are you sure you want to delete this post? This action cannot be undone."
        )
    ) {
        return;
    }

    const message =
        document.getElementById(
            "editPostMessage"
        );

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/posts/${postId}`,
                {
                    method: "DELETE",

                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`,
                    },
                }
            );

        const responseText =
            await response.text();

        let data = {};

        try {
            data =
                responseText
                    ? JSON.parse(responseText)
                    : {};
        } catch (error) {
            data = {};
        }

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to delete post"
            );
        }

        editingPost = null;
        selectedEditImages = [];

        document
            .getElementById(
                "editPostSection"
            )
            .classList.add("hidden");

        document
            .getElementById(
                "editPostForm"
            )
            .reset();

        document.getElementById(
            "editImagesContainer"
        ).innerHTML = "";

        document.getElementById(
            "editImageSelection"
        ).textContent = "";

        if (message) {
            message.textContent =
                "Post deleted successfully.";

            message.className =
                "message success-message";
        }

        await loadPosts();

        const showAllButton =
            document.getElementById(
                "showAllPostsButton"
            );

        if (
            showAllButton &&
            !showAllButton.classList.contains(
                "hidden"
            )
        ) {
            await showMyPosts();
        }

        await loadDashboard();

    } catch (error) {
        if (message) {
            message.textContent =
                error.message;

            message.className =
                "message error-message";
        } else {
            alert(error.message);
        }
    }
}


async function deletePostImage(
    postId,
    imageId
) {
    if (!confirm(
        "Are you sure you want to delete this image?"
    )) {
        return;
    }

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/posts/${postId}/images/${imageId}`,
                {
                    method: "DELETE",

                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`,
                    },
                }
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to delete image"
            );
        }

        editingPost =
            data;

        renderEditImages(
            editingPost
        );

        updateImageLimitHints();

        await loadPosts();
        await loadDashboard();

    } catch (error) {
        alert(error.message);
    }
}


function cancelEditPost() {
    editingPost = null;
    selectedEditImages = [];

    document
        .getElementById("editPostSection")
        .classList.add("hidden");

    document
        .getElementById("editPostForm")
        .reset();

    document.getElementById(
        "editImagesContainer"
    ).innerHTML = "";

    document.getElementById(
        "editImageSelection"
    ).textContent = "";

    document.getElementById(
        "editPostMessage"
    ).textContent = "";
}


async function addComment(postId) {
    if (!accessToken) {
        alert(
            "Please login to add a comment."
        );

        return;
    }

    const commentInput =
        document.getElementById(
            `comment-input-${postId}`
        );

    const text =
        commentInput.value.trim();

    if (!text) {
        alert(
            "Please enter a comment."
        );

        return;
    }

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/posts/${postId}/comments/`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${accessToken}`,
                    },

                    body: JSON.stringify({
                        text,
                    }),
                }
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to add comment"
            );
        }

        commentInput.value = "";

        await viewComments(postId);
        await loadDashboard();

    } catch (error) {
        alert(error.message);
    }
}


async function likePost(postId) {
    if (!accessToken) {
        alert(
            "Please login to like a post."
        );

        return;
    }

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/posts/${postId}/likes/`,
                {
                    method: "POST",

                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`,
                    },
                }
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to like post"
            );
        }

        alert(data.message);

        await loadDashboard();

    } catch (error) {
        alert(error.message);
    }
}


async function unlikePost(postId) {
    if (!accessToken) {
        alert(
            "Please login to unlike a post."
        );

        return;
    }

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/posts/${postId}/likes/`,
                {
                    method: "DELETE",

                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`,
                    },
                }
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to unlike post"
            );
        }

        alert(data.message);

        await loadDashboard();

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
        const response =
            await fetch(
                `${API_BASE_URL}/posts/${postId}/comments/`
            );

        const comments =
            await response.json();

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
                            ${escapeHtml(
                                comment.text
                            )}
                        </p>

                        <small>
                            ${formatDate(
                                comment.created_at
                            )}
                        </small>

                    </div>
                `
            ).join("");

    } catch (error) {
        commentsContainer.innerHTML =
            `<p class="error-message">${escapeHtml(
                error.message
            )}</p>`;
    }
}


function getMediaUrl(path) {
    if (!path) {
        return "";
    }

    if (
        path.startsWith("http://") ||
        path.startsWith("https://")
    ) {
        return path;
    }

    if (path.startsWith("/")) {
        return `${API_BASE_URL}${path}`;
    }

    if (path.startsWith("media/")) {
        return `${API_BASE_URL}/${path}`;
    }

    return `${API_BASE_URL}/media/posts/${path}`;
}


function formatDate(dateString) {
    return new Date(
        dateString
    ).toLocaleString();
}


function escapeHtml(value) {
    const div =
        document.createElement("div");

    div.textContent =
        value ?? "";

    return div.innerHTML;
}


document.addEventListener(
    "DOMContentLoaded",
    () => {
        const createInput =
            document.getElementById(
                "createPostImages"
            );

        const editInput =
            document.getElementById(
                "editPostImages"
            );

        if (createInput) {
            createInput.addEventListener(
                "change",
                handleCreateImageSelection
            );
        }

        if (editInput) {
            editInput.addEventListener(
                "change",
                handleEditImageSelection
            );
        }
    }
);


async function loadNotifications() {
    if (!accessToken) {
        return;
    }

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/notifications/`,
                {
                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`,
                    },
                }
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to load notifications"
            );
        }

        renderNotifications(data);

        await loadUnreadNotificationCount();

    } catch (error) {
        console.error(
            "Notification loading error:",
            error
        );
    }
}


async function loadUnreadNotificationCount() {
    if (!accessToken) {
        return;
    }

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/notifications/unread-count`,
                {
                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`,
                    },
                }
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to load unread notification count"
            );
        }

        updateNotificationBadge(
            data.unread_count
        );

    } catch (error) {
        console.error(
            "Unread notification count error:",
            error
        );
    }
}


function updateNotificationBadge(unreadCount) {
    const badge =
        document.getElementById(
            "notificationBadge"
        );

    if (!badge) {
        return;
    }

    if (unreadCount > 0) {
        badge.textContent =
            unreadCount > 99
                ? "99+"
                : unreadCount;

        badge.classList.remove("hidden");
    } else {
        badge.textContent = "0";
        badge.classList.add("hidden");
    }
}


function renderNotifications(notifications) {
    const list =
        document.getElementById(
            "notificationList"
        );

    const summary =
        document.getElementById(
            "notificationSummary"
        );

    if (!list || !summary) {
        return;
    }

    if (
        !Array.isArray(notifications) ||
        notifications.length === 0
    ) {
        list.innerHTML = `
            <p class="notification-empty">
                No notifications yet.
            </p>
        `;

        summary.textContent =
            "No notifications";

        return;
    }

    const unreadCount =
        notifications.filter(
            (notification) =>
                !notification.is_read
        ).length;

    summary.textContent =
        unreadCount > 0
            ? `${unreadCount} unread notification${unreadCount === 1 ? "" : "s"}`
            : "All notifications are read";

    list.innerHTML =
        notifications
            .map(
                (notification) => {
                    const icon =
                        getNotificationIcon(
                            notification.notification_type
                        );

                    const readClass =
                        notification.is_read
                            ? "read"
                            : "unread";

                    const actionText =
                        notification.is_read
                            ? "Mark unread"
                            : "Mark read";

                    return `
                        <div
                            class="notification-item ${readClass}"
                        >

                            <div class="notification-icon">
                                ${icon}
                            </div>

                            <div class="notification-content">

                                <p class="notification-message">
                                    ${escapeHtml(
                                        notification.message
                                    )}
                                </p>

                                <span class="notification-time">
                                    ${formatNotificationDate(
                                        notification.created_at
                                    )}
                                </span>

                                <button
                                    class="notification-action"
                                    onclick="toggleNotificationReadStatus(${notification.id}, ${notification.is_read})"
                                >
                                    ${actionText}
                                </button>

                            </div>

                        </div>
                    `;
                }
            )
            .join("");
}


function getNotificationIcon(type) {
    switch (type) {
        case "like":
            return "❤️";

        case "comment":
            return "💬";

        case "subscription":
            return "💳";

        default:
            return "🔔";
    }
}


function formatNotificationDate(dateString) {
    const date =
        new Date(dateString);

    const now =
        new Date();

    const difference =
        Math.floor(
            (now - date) / 1000
        );

    if (difference < 60) {
        return "Just now";
    }

    if (difference < 3600) {
        const minutes =
            Math.floor(
                difference / 60
            );

        return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
    }

    if (difference < 86400) {
        const hours =
            Math.floor(
                difference / 3600
            );

        return `${hours} hour${hours === 1 ? "" : "s"} ago`;
    }

    if (difference < 604800) {
        const days =
            Math.floor(
                difference / 86400
            );

        return `${days} day${days === 1 ? "" : "s"} ago`;
    }

    return date.toLocaleString();
}


function toggleNotificationDropdown(event) {
    if (event) {
        event.stopPropagation();
    }

    const dropdown =
        document.getElementById(
            "notificationDropdown"
        );

    const bell =
        document.getElementById(
            "notificationBell"
        );

    if (!dropdown || !bell) {
        return;
    }

    notificationDropdownOpen =
        !notificationDropdownOpen;

    if (notificationDropdownOpen) {
        dropdown.classList.remove("hidden");

        bell.setAttribute(
            "aria-expanded",
            "true"
        );

        loadNotifications();
    } else {
        dropdown.classList.add("hidden");

        bell.setAttribute(
            "aria-expanded",
            "false"
        );
    }
}


function closeNotificationDropdown() {
    const dropdown =
        document.getElementById(
            "notificationDropdown"
        );

    const bell =
        document.getElementById(
            "notificationBell"
        );

    notificationDropdownOpen =
        false;

    if (dropdown) {
        dropdown.classList.add("hidden");
    }

    if (bell) {
        bell.setAttribute(
            "aria-expanded",
            "false"
        );
    }
}


async function toggleNotificationReadStatus(
    notificationId,
    isRead
) {
    if (!accessToken) {
        return;
    }

    const endpoint =
        isRead
            ? `${API_BASE_URL}/notifications/${notificationId}/unread`
            : `${API_BASE_URL}/notifications/${notificationId}/read`;

    try {
        const response =
            await fetch(
                endpoint,
                {
                    method: "PATCH",

                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`,
                    },
                }
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to update notification"
            );
        }

        await loadNotifications();

    } catch (error) {
        console.error(
            "Notification status error:",
            error
        );
    }
}


async function markAllNotificationsAsRead() {
    if (!accessToken) {
        return;
    }

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/notifications/read-all`,
                {
                    method: "PATCH",

                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`,
                    },
                }
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to mark all notifications as read"
            );
        }

        await loadNotifications();

    } catch (error) {
        console.error(
            "Mark all notifications error:",
            error
        );
    }
}


function startNotificationPolling() {
    stopNotificationPolling();

    if (!accessToken) {
        return;
    }

    notificationPollingInterval =
        setInterval(
            async () => {
                if (accessToken) {
                    await loadUnreadNotificationCount();

                    if (notificationDropdownOpen) {
                        await loadNotifications();
                    }
                }
            },
            15000
        );
}


function stopNotificationPolling() {
    if (
        notificationPollingInterval !== null
    ) {
        clearInterval(
            notificationPollingInterval
        );

        notificationPollingInterval =
            null;
    }
}


document.addEventListener(
    "click",
    (event) => {
        const notificationCenter =
            document.getElementById(
                "notificationCenter"
            );

        if (
            notificationCenter &&
            !notificationCenter.contains(
                event.target
            )
        ) {
            closeNotificationDropdown();
        }
    }
);


document.addEventListener(
    "keydown",
    (event) => {
        if (event.key === "Escape") {
            closeNotificationDropdown();
        }
    }
);


let aiSupportChatOpen = false;


function updateAISupportVisibility() {
    const widget =
        document.getElementById("aiSupportWidget");

    if (!widget) {
        return;
    }

    if (accessToken) {
        widget.classList.remove("hidden");
    } else {
        widget.classList.add("hidden");
        closeAISupportChat();
    }
}


function toggleAISupportChat() {
    if (!accessToken) {
        return;
    }

    const panel =
        document.getElementById("aiSupportPanel");

    const toggle =
        document.getElementById("aiSupportToggle");

    if (!panel || !toggle) {
        return;
    }

    aiSupportChatOpen =
        !aiSupportChatOpen;

    if (aiSupportChatOpen) {
        panel.classList.remove("hidden");

        toggle.setAttribute(
            "aria-expanded",
            "true"
        );

        loadAISupportHistory();

        setTimeout(() => {
            const input =
                document.getElementById("aiSupportInput");

            if (input) {
                input.focus();
            }
        }, 100);
    } else {
        panel.classList.add("hidden");

        toggle.setAttribute(
            "aria-expanded",
            "false"
        );
    }
}


function closeAISupportChat() {
    const panel =
        document.getElementById("aiSupportPanel");

    const toggle =
        document.getElementById("aiSupportToggle");

    aiSupportChatOpen = false;

    if (panel) {
        panel.classList.add("hidden");
    }

    if (toggle) {
        toggle.setAttribute(
            "aria-expanded",
            "false"
        );
    }
}


function appendAISupportMessage(
    message,
    sender
) {
    const container =
        document.getElementById(
            "aiSupportMessages"
        );

    if (!container) {
        return;
    }

    const wrapper =
        document.createElement("div");

    wrapper.className =
        sender === "user"
            ? "ai-support-message ai-support-message-user"
            : "ai-support-message ai-support-message-bot";

    if (sender === "user") {
        const bubble =
            document.createElement("div");

        bubble.className =
            "ai-support-bubble";

        bubble.textContent =
            message;

        wrapper.appendChild(
            bubble
        );
    } else {
        const avatar =
            document.createElement("div");

        avatar.className =
            "ai-support-avatar";

        avatar.textContent =
            "🤖";

        const bubble =
            document.createElement("div");

        bubble.className =
            "ai-support-bubble";

        bubble.textContent =
            message;

        wrapper.appendChild(
            avatar
        );

        wrapper.appendChild(
            bubble
        );
    }

    container.appendChild(
        wrapper
    );

    container.scrollTop =
        container.scrollHeight;
}


async function sendAISupportMessage(event) {
    event.preventDefault();

    if (!accessToken) {
        return;
    }

    const input =
        document.getElementById(
            "aiSupportInput"
        );

    const sendButton =
        document.getElementById(
            "aiSupportSendButton"
        );

    if (!input || !sendButton) {
        return;
    }

    const message =
        input.value.trim();

    if (!message) {
        return;
    }

    appendAISupportMessage(
        message,
        "user"
    );

    input.value = "";

    sendButton.disabled = true;
    sendButton.textContent = "Sending...";

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/api/ai-support/`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${accessToken}`,
                    },

                    body: JSON.stringify({
                        message,
                    }),
                }
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to get AI Support response"
            );
        }

        appendAISupportMessage(
            data.response,
            "bot"
        );

        await loadAISupportHistory();

    } catch (error) {
        appendAISupportMessage(
            error.message ||
            "Unable to connect to AI Support.",
            "bot"
        );
    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "Send";

        input.focus();
    }
}


async function loadAISupportHistory() {
    if (!accessToken) {
        return;
    }

    const container =
        document.getElementById(
            "aiSupportHistory"
        );

    if (!container) {
        return;
    }

    container.innerHTML =
        '<p class="ai-support-history-empty">Loading conversations...</p>';

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/api/ai-support/history`,
                {
                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`,
                    },
                }
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to load AI Support history"
            );
        }

        if (
            !Array.isArray(data) ||
            data.length === 0
        ) {
            container.innerHTML =
                '<p class="ai-support-history-empty">No previous conversations.</p>';

            return;
        }

        container.innerHTML =
            data
                .map(
                    (chat) => `
                        <div class="ai-support-history-item">
                            <div class="ai-support-history-question">
                                ${escapeHtml(chat.question)}
                            </div>

                            <div class="ai-support-history-response">
                                ${escapeHtml(chat.response)}
                            </div>

                            <div class="ai-support-history-time">
                                ${formatAISupportDate(chat.created_at)}
                            </div>
                        </div>
                    `
                )
                .join("");

    } catch (error) {
        container.innerHTML =
            `<p class="ai-support-history-empty">${escapeHtml(
                error.message ||
                "Unable to load conversations."
            )}</p>`;
    }
}


function formatAISupportDate(dateString) {
    if (!dateString) {
        return "";
    }

    const date =
        new Date(dateString);

    if (Number.isNaN(date.getTime())) {
        return "";
    }

    return date.toLocaleString();
}


document.addEventListener(
    "keydown",
    (event) => {
        if (event.key === "Escape") {
            closeAISupportChat();
        }
    }
);


function clearAISupportMessages() {
    const container =
        document.getElementById(
            "aiSupportMessages"
        );

    if (!container) {
        return;
    }

    container.innerHTML = `
        <div class="ai-support-message ai-support-message-bot">
            <div class="ai-support-avatar">🤖</div>

            <div class="ai-support-bubble">
                Chat cleared. How can I help you?
            </div>
        </div>
    `;
}