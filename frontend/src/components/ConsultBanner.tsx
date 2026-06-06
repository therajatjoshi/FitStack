interface ConsultBannerProps {
  consult_recommended: boolean;
  disclaimer: string;
}

export default function ConsultBanner({
  consult_recommended,
  disclaimer,
}: ConsultBannerProps) {
  if (!consult_recommended && !disclaimer) return null;

  return (
    <div>
      {consult_recommended && (
        <div className="consult-banner">
          ⚠️ Based on your health information, we recommend clearing this
          program with a healthcare professional before starting.
        </div>
      )}
      {disclaimer && (
        <p className="consult-disclaimer">{disclaimer}</p>
      )}
    </div>
  );
}
