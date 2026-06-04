// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const getFirebaseErrorMessage = (error: any): string => {
  if (!error || !error.code) {
    return "An unknown error occurred. Please try again.";
  }

  switch (error.code) {
    case "auth/email-already-in-use":
      return "This email is already in use. Please use a different one or sign in.";
    case "auth/invalid-email":
      return "The email address is not valid.";
    case "auth/user-disabled":
      return "This user account has been disabled.";
    case "auth/user-not-found":
    case "auth/wrong-password":
    case "auth/invalid-credential":
      return "Invalid email or password.";
    case "auth/weak-password":
      return "The password is too weak. Please use a stronger password.";
    case "auth/too-many-requests":
      return "Too many attempts. Please try again later.";
    case "auth/network-request-failed":
      return "Network error. Please check your connection.";
    default:
      return error.message || "An unexpected error occurred.";
  }
};
