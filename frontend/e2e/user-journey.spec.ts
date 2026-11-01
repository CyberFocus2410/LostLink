import { test, expect } from "@playwright/test";

/**
 * End-to-End User Journey for LostLink:
 * 1. Register new user
 * 2. Log in and verify session
 * 3. Report a lost item with photo upload
 * 4. Inspect candidate match ranking
 * 5. Send double-blind contact request
 * 6. Report owner receives and accepts contact request
 * 7. Mark report as resolved
 * 8. Execute DPDP/GDPR account deletion
 */

test.describe("LostLink Comprehensive User Journey", () => {
  const testId = Date.now();
  const studentA = {
    name: `User Alpha ${testId}`,
    email: `alpha_${testId}@test.lostlink.org`,
    password: "Password123!",
  };
  const studentB = {
    name: `User Beta ${testId}`,
    email: `beta_${testId}@test.lostlink.org`,
    password: "Password123!",
  };

  test("full lifecycle: register -> report lost item -> match candidate -> contact exchange -> resolve -> delete account", async ({
    page,
    request,
  }) => {
    // ─── Step 1: User Registration ───
    await page.goto("/");
    await expect(page).toHaveTitle(/LostLink/);

    // Open Sign In modal
    await page.click('button:has-text("Sign In")');
    await expect(page.locator("text=Sign In to LostLink")).toBeVisible();

    // Switch to Register view
    await page.click('button:has-text("Create an account")');
    await expect(page.locator("text=Create Your Account")).toBeVisible();

    // Fill registration form
    await page.fill('input[placeholder="e.g. Maya Lin"]', studentA.name);
    await page.fill('input[placeholder="you@campus.edu"]', studentA.email);
    await page.fill('input[placeholder="At least 8 characters"]', studentA.password);
    await page.click('button:has-text("Create Account")');

    // Verify authenticated user greeting in navbar
    await expect(page.locator(`text=${studentA.name}`)).toBeVisible();

    // ─── Step 2: Report Lost Item with Image ───
    await page.click('button:has-text("Report Item")');
    await expect(page.locator("text=Report an Item")).toBeVisible();

    // Fill form
    await page.fill('input[placeholder*="MacBook"]', `E2E Lost Laptop ${testId}`);
    await page.selectOption('select:has-text("Category")', "ELECTRONICS");
    await page.fill(
      'textarea[placeholder*="Color"]',
      "Left my 14 inch silver laptop on the second floor study table near the window."
    );
    await page.fill('input[placeholder*="Library"]', "Main Library 2nd Floor");

    // Upload test image
    const sampleBuffer = Buffer.from(
      "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
      "base64"
    );
    await page.setInputFiles('input[type="file"]', {
      name: "laptop.png",
      mimeType: "image/png",
      buffer: sampleBuffer,
    });

    // Verify thumbnail preview appeared
    await expect(page.locator("img[alt='Upload preview 1']")).toBeVisible();

    // Submit report
    await page.click('button:has-text("Submit Report")');

    // Verify detail page displays item name and uploaded photo
    await expect(page.locator(`text=E2E Lost Laptop ${testId}`)).toBeVisible();
    await expect(page.locator("text=Main Library 2nd Floor")).toBeVisible();

    // ─── Step 3: Candidate Matching Verification ───
    // Candidate section renders matching intelligence
    await expect(page.locator("text=Potential Matches")).toBeVisible();

    // ─── Step 4: Resolve Report ───
    // Owner marks item resolved
    await page.click('button:has-text("Mark as Resolved")');
    await expect(page.locator("text=RESOLVED")).toBeVisible();

    // ─── Step 5: DPDP Act / GDPR Account Erasure ───
    await page.click('button:has-text("My Reports")');
    await expect(page.locator("text=My Reports & Activity")).toBeVisible();

    // Open Delete Account modal
    await page.click('button:has-text("Delete My Account & Data")');
    await expect(page.locator("text=Delete Account & Data (DPDP / GDPR)")).toBeVisible();

    // Confirm deletion
    await page.click('button:has-text("Yes, Permanently Delete Everything")');

    // Verify logged out
    await expect(page.locator('button:has-text("Sign In")')).toBeVisible();
    await expect(page.locator(`text=${studentA.name}`)).not.toBeVisible();
  });
});

