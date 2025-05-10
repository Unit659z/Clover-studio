import React from "react";

interface ReviewCardProps {
  avatar_url: string | null;
  name: string;
  stars: number;
  reviewText: string;
}

const DEFAULT_AVATAR_IMAGE = "/images/placeholder-avatar.png";

const ReviewCard: React.FC<ReviewCardProps> = ({
  avatar_url,
  name,
  stars,
  reviewText,
}) => {
  const renderStars = () => {
    let starElements = [];
    for (let i = 0; i < 5; i++) {
      starElements.push(
        <span
          key={i}
          className={i < stars ? "text-[#EB0000]" : "text-gray-400"}
        >
          ★
        </span>
      );
    }
    return starElements;
  };

  return (
    <div className="bg-white text-[#181818] rounded-lg p-6 shadow-lg text-center transform transition duration-300 hover:-translate-y-1">
      <img
        src={avatar_url || DEFAULT_AVATAR_IMAGE}
        alt={name}
        className="w-16 h-16 rounded-full mx-auto mb-3 border-2 border-gray-300 object-cover bg-gray-200"
        onError={(e) => {
          const target = e.target as HTMLImageElement;
          target.onerror = null;
          target.src = DEFAULT_AVATAR_IMAGE;
        }}
      />
      <h4 className="font-semibold text-lg mb-1">{name}</h4>
      <div className="flex justify-center mb-2">{renderStars()}</div>
      <p className="text-sm text-gray-600 italic">"{reviewText}"</p>
    </div>
  );
};

export default ReviewCard;
