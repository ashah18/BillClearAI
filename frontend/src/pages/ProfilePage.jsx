import { useState, useEffect } from "react";
import Navbar from "../components/Navbar.jsx";
import { getProfile, updateProfile } from "../api/user.js";
import { changePassword } from "../api/auth.js";
import { setAccessToken } from "../api/axios.js";
import { useToast } from "../context/ToastContext.jsx";

const US_STATES = [
  "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
  "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
  "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
  "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
  "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
  "DC",
];

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
    </div>
  );
}

const inputClass =
  "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent";

export default function ProfilePage() {
  const { addToast } = useToast();

  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    street_address: "",
    city: "",
    state: "",
    zip_code: "",
    phone_number: "",
    date_of_birth: "",
    insurance_provider: "",
    plan_type: "",
  });
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [profileError, setProfileError] = useState("");

  // Change-password form state
  const [pwForm, setPwForm] = useState({ current_password: "", new_password: "", confirm_password: "" });
  const [isSavingPw, setIsSavingPw] = useState(false);
  const [pwError, setPwError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await getProfile();
        setEmail(data.email || "");
        setForm({
          first_name: data.first_name || "",
          last_name: data.last_name || "",
          street_address: data.street_address || "",
          city: data.city || "",
          state: data.state || "",
          zip_code: data.zip_code || "",
          phone_number: data.phone_number || "",
          date_of_birth: data.date_of_birth || "",
          insurance_provider: data.insurance_provider || "",
          plan_type: data.plan_type || "",
        });
      } catch {
        setProfileError("Failed to load profile.");
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setIsSaving(true);
    setProfileError("");
    try {
      await updateProfile(form);
      addToast("Profile saved successfully");
    } catch {
      setProfileError("Failed to save profile. Please try again.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleChangePassword(e) {
    e.preventDefault();
    setPwError("");

    if (pwForm.new_password !== pwForm.confirm_password) {
      setPwError("New passwords do not match.");
      return;
    }

    setIsSavingPw(true);
    try {
      const data = await changePassword(pwForm.current_password, pwForm.new_password);
      // Server returns a new access token — update the in-memory token
      if (data.access) {
        setAccessToken(data.access);
      }
      setPwForm({ current_password: "", new_password: "", confirm_password: "" });
      addToast("Password updated");
    } catch (err) {
      const msg =
        err.response?.data?.current_password?.[0] ||
        err.response?.data?.new_password?.[0] ||
        err.response?.data?.detail ||
        "Failed to change password. Please try again.";
      setPwError(msg);
    } finally {
      setIsSavingPw(false);
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="text-center py-24 text-gray-400">Loading profile...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Your Profile</h1>
          <p className="text-sm text-gray-500 mt-1">
            This information is used to auto-fill your dispute letters.
          </p>
        </div>

        {profileError && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {profileError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Account info (read-only) */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-4">
            <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">Account</h2>
            <Field label="Email">
              <input
                type="email"
                value={email}
                disabled
                className={`${inputClass} bg-gray-50 text-gray-400 cursor-not-allowed`}
              />
            </Field>
          </div>

          {/* Personal info */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-4">
            <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">Personal Information</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="First Name">
                <input
                  type="text"
                  name="first_name"
                  value={form.first_name}
                  onChange={handleChange}
                  className={inputClass}
                  placeholder="Jane"
                />
              </Field>
              <Field label="Last Name">
                <input
                  type="text"
                  name="last_name"
                  value={form.last_name}
                  onChange={handleChange}
                  className={inputClass}
                  placeholder="Smith"
                />
              </Field>
            </div>
            <Field label="Date of Birth">
              <input
                type="date"
                name="date_of_birth"
                value={form.date_of_birth}
                onChange={handleChange}
                className={inputClass}
              />
            </Field>
            <Field label="Phone Number">
              <input
                type="tel"
                name="phone_number"
                value={form.phone_number}
                onChange={handleChange}
                className={inputClass}
                placeholder="(555) 555-5555"
              />
            </Field>
          </div>

          {/* Address */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-4">
            <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">Address</h2>
            <Field label="Street Address">
              <input
                type="text"
                name="street_address"
                value={form.street_address}
                onChange={handleChange}
                className={inputClass}
                placeholder="123 Main St"
              />
            </Field>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Field label="City">
                <input
                  type="text"
                  name="city"
                  value={form.city}
                  onChange={handleChange}
                  className={inputClass}
                  placeholder="Springfield"
                />
              </Field>
              <Field label="State">
                <select
                  name="state"
                  value={form.state}
                  onChange={handleChange}
                  className={inputClass}
                >
                  <option value="">—</option>
                  {US_STATES.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </Field>
              <Field label="ZIP Code">
                <input
                  type="text"
                  name="zip_code"
                  value={form.zip_code}
                  onChange={handleChange}
                  className={inputClass}
                  placeholder="62701"
                  maxLength={10}
                />
              </Field>
            </div>
          </div>

          {/* Insurance */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-4">
            <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">Insurance</h2>
            <Field label="Insurance Provider">
              <input
                type="text"
                name="insurance_provider"
                value={form.insurance_provider}
                onChange={handleChange}
                className={inputClass}
                placeholder="Blue Cross Blue Shield"
              />
            </Field>
            <Field label="Plan Type">
              <input
                type="text"
                name="plan_type"
                value={form.plan_type}
                onChange={handleChange}
                className={inputClass}
                placeholder="PPO, HMO, EPO…"
              />
            </Field>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isSaving}
              className="w-full sm:w-auto bg-blue-600 text-white text-sm font-medium px-6 py-2.5 rounded-lg hover:bg-blue-700 disabled:opacity-60 transition-colors"
            >
              {isSaving ? "Saving…" : "Save Profile"}
            </button>
          </div>
        </form>

        {/* Change Password — separate form */}
        <form onSubmit={handleChangePassword} className="mt-6">
          <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-4">
            <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">Change Password</h2>

            {pwError && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {pwError}
              </div>
            )}

            <Field label="Current Password">
              <input
                type="password"
                value={pwForm.current_password}
                onChange={(e) => setPwForm((p) => ({ ...p, current_password: e.target.value }))}
                className={inputClass}
                placeholder="Your current password"
                autoComplete="current-password"
              />
            </Field>
            <Field label="New Password">
              <input
                type="password"
                value={pwForm.new_password}
                onChange={(e) => setPwForm((p) => ({ ...p, new_password: e.target.value }))}
                className={inputClass}
                placeholder="At least 8 characters"
                minLength={8}
                autoComplete="new-password"
              />
            </Field>
            <Field label="Confirm New Password">
              <input
                type="password"
                value={pwForm.confirm_password}
                onChange={(e) => setPwForm((p) => ({ ...p, confirm_password: e.target.value }))}
                className={inputClass}
                placeholder="Repeat your new password"
                autoComplete="new-password"
              />
            </Field>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={isSavingPw}
                className="w-full sm:w-auto bg-gray-800 text-white text-sm font-medium px-6 py-2.5 rounded-lg hover:bg-gray-900 disabled:opacity-60 transition-colors"
              >
                {isSavingPw ? "Updating…" : "Update Password"}
              </button>
            </div>
          </div>
        </form>
      </main>
    </div>
  );
}
