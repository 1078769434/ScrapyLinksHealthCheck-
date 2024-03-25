from typing import Optional

from sqlalchemy import func
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
Base = declarative_base()

class Urls(Base):
    # 页面
    __tablename__ = "urls"
    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, index=True)
    url: Mapped[Optional[str]] = mapped_column(sa.String(128), nullable=True, comment="页面地址")
    category: Mapped[Optional[str]] = mapped_column(sa.String(128), comment="页面分类")
    status_code: Mapped[Optional[int]] = mapped_column(sa.Integer, comment="状态码")
    etag: Mapped[Optional[str]] = mapped_column(sa.String(256), comment="生成给定页面内容的ETag")
    last_modified: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, comment="页面最后修改时间")
    is_external: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False, index=True,
                                              comment="是否为外链url")
    referer: Mapped[Optional[str]] = mapped_column(sa.Text, comment="父页面")
    crawl_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, default=func.now(),comment="页面最后爬取时间")
    update_at: Mapped[datetime] = mapped_column(sa.DateTime, onupdate=func.now(), comment="页面最后修改时间")